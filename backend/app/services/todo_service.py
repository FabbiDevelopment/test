import uuid
from datetime import datetime

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import Tag
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoStatus


async def create_todo(
    db: AsyncSession, todo_data: TodoCreate, user_id: uuid.UUID
) -> Todo:
    todo = Todo(
        title=todo_data.title,
        description=todo_data.description,
        user_id=user_id,
        tags=[],
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
    status: TodoStatus | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Todo], int]:
    """Get all todos with pagination for a specific user."""
    filters = [Todo.user_id == user_id]

    if status == "completed":
        filters.append(Todo.completed.is_(True))
    elif status == "active":
        filters.append(Todo.completed.is_(False))

    if tag_id is not None:
        filters.append(Todo.tags.any(and_(Tag.id == tag_id, Tag.user_id == user_id)))

    if keyword:
        search_term = f"%{keyword.strip()}%"
        filters.append(
            or_(
                Todo.title.ilike(search_term),
                Todo.description.ilike(search_term),
            )
        )

    if date_from is not None:
        filters.append(Todo.created_at >= date_from)
    if date_to is not None:
        filters.append(Todo.created_at <= date_to)

    query = (
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(*filters)
        .order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    todos = list(result.scalars().all())

    # Count total
    count_query = select(func.count()).select_from(Todo).where(*filters)
    total = await db.execute(count_query)

    return todos, total.scalar_one()


async def get_todo_by_id(
    db: AsyncSession, todo_id: uuid.UUID, user_id: uuid.UUID
) -> Todo | None:
    result = await db.execute(
        select(Todo)
        .options(selectinload(Todo.tags))
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


async def bulk_update_todo_status(
    db: AsyncSession,
    todo_ids: list[uuid.UUID],
    completed: bool,
    user_id: uuid.UUID,
) -> list[Todo] | None:
    owned_count = await db.scalar(
        select(func.count())
        .select_from(Todo)
        .where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
    )
    if owned_count != len(todo_ids):
        return None

    result = await db.execute(
        update(Todo)
        .where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
        .values(completed=completed, updated_at=func.now())
    )
    if result.rowcount != len(todo_ids):
        return None

    updated = await db.execute(
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
        .order_by(Todo.created_at.desc(), Todo.id.desc())
    )
    return list(updated.scalars().all())
