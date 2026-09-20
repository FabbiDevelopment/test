import re
import uuid
from datetime import datetime

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from app.models.tag import Tag, TodoTag
from app.models.todo import Todo
from app.schemas.todo import TodoCreate


async def create_todo(
    db: AsyncSession, todo_data: TodoCreate, user_id: uuid.UUID
) -> Todo:
    todo = Todo(
        title=todo_data.title,
        description=todo_data.description,
        user_id=user_id,
    )
    db.add(todo)
    await db.flush()
    await db.refresh(todo)
    return todo


async def get_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    status: bool | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Todo], int]:
    """Get all todos with filtering and pagination for a specific user."""
    query = (
        select(Todo)
        .options(
            selectinload(Todo.tags).load_only(Tag.id, Tag.name, Tag.color)
        )
        .where(Todo.user_id == user_id)
    )
    count_query = select(func.count()).select_from(Todo).where(Todo.user_id == user_id)

    # Filter by completed status
    if status is not None:
        query = query.where(Todo.completed == status)
        count_query = count_query.where(Todo.completed == status)

    # Filter by tag
    if tag_id is not None:
        tag_subquery = select(TodoTag.todo_id).where(TodoTag.tag_id == tag_id)
        query = query.where(Todo.id.in_(tag_subquery))
        count_query = count_query.where(Todo.id.in_(tag_subquery))

    # Filter by keyword in title or description (accelerated by PostgreSQL pg_trgm GIN index)
    if keyword and keyword.strip():
        clean_kw = keyword.strip()
        escaped_kw = (
            clean_kw.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        search_pattern = f"%{escaped_kw}%"
        search_filter = or_(
            Todo.title.ilike(search_pattern),
            Todo.description.ilike(search_pattern),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)



    # Filter by date range (created_at)
    if date_from is not None:
        query = query.where(Todo.created_at >= date_from)
        count_query = count_query.where(Todo.created_at >= date_from)

    if date_to is not None:
        query = query.where(Todo.created_at <= date_to)
        count_query = count_query.where(Todo.created_at <= date_to)

    # Ordering and pagination
    query = (
        query.order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    todos = list(result.scalars().all())

    # Count total
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    return todos, total


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    result = await db.execute(
        select(Todo)
        .options(
            selectinload(Todo.tags).load_only(Tag.id, Tag.name, Tag.color)
        )
        .where(Todo.id == todo_id)
    )
    return result.scalar_one_or_none()


async def get_todo_by_id_and_user(
    db: AsyncSession, todo_id: uuid.UUID, user_id: uuid.UUID
) -> Todo | None:
    result = await db.execute(
        select(Todo)
        .options(
            selectinload(Todo.tags).load_only(Tag.id, Tag.name, Tag.color)
        )
        .where(Todo.id == todo_id, Todo.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    for key, value in update_data.items():
        setattr(todo, key, value)
    await db.flush()
    await db.refresh(todo)
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()


BULK_CHUNK_SIZE = 500


async def bulk_update_status(
    db: AsyncSession,
    user_id: uuid.UUID,
    todo_ids: list[uuid.UUID],
    completed: bool,
) -> int:
    """Bulk update completed status in chunks within an explicit transaction with rollback."""
    total_updated = 0
    try:
        for i in range(0, len(todo_ids), BULK_CHUNK_SIZE):
            chunk = todo_ids[i : i + BULK_CHUNK_SIZE]
            stmt = (
                update(Todo)
                .where(Todo.user_id == user_id, Todo.id.in_(chunk))
                .values(completed=completed)
            )
            result = await db.execute(stmt)
            total_updated += result.rowcount
        await db.flush()
        return total_updated
    except Exception:
        await db.rollback()
        raise


async def bulk_delete_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    todo_ids: list[uuid.UUID],
) -> int:
    """Bulk delete todos in chunks within an explicit transaction with rollback."""
    total_deleted = 0
    try:
        for i in range(0, len(todo_ids), BULK_CHUNK_SIZE):
            chunk = todo_ids[i : i + BULK_CHUNK_SIZE]
            # Clean up todo_tags associations for the user's todos
            user_todos_subquery = (
                select(Todo.id)
                .where(Todo.user_id == user_id, Todo.id.in_(chunk))
            )
            tag_stmt = delete(TodoTag).where(TodoTag.todo_id.in_(user_todos_subquery))
            await db.execute(tag_stmt)

            stmt = (
                delete(Todo)
                .where(Todo.user_id == user_id, Todo.id.in_(chunk))
            )
            result = await db.execute(stmt)
            total_deleted += result.rowcount
        await db.flush()
        return total_deleted
    except Exception:
        await db.rollback()
        raise

