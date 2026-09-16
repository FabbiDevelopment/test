import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import TodoTag
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
    # Ensure tags relationship is initialized
    todo.tags = []
    return todo


async def get_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Todo], int]:
    """Get all todos with pagination, advanced filtering, and eager-loaded tags."""
    query = (
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.user_id == user_id)
    )
    count_query = select(func.count(Todo.id.distinct())).select_from(Todo).where(Todo.user_id == user_id)

    # Filter: completion status
    if status == "completed":
        query = query.where(Todo.completed.is_(True))
        count_query = count_query.where(Todo.completed.is_(True))
    elif status == "active":
        query = query.where(Todo.completed.is_(False))
        count_query = count_query.where(Todo.completed.is_(False))

    # Filter: tag
    if tag_id is not None:
        query = query.join(TodoTag, TodoTag.todo_id == Todo.id).where(TodoTag.tag_id == tag_id)
        count_query = count_query.join(TodoTag, TodoTag.todo_id == Todo.id).where(TodoTag.tag_id == tag_id)

    # Filter: keyword (search in title or description)
    if keyword and keyword.strip():
        search_pattern = f"%{keyword.strip()}%"
        search_filter = or_(
            Todo.title.ilike(search_pattern),
            Todo.description.ilike(search_pattern),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Filter: date range
    if date_from is not None:
        query = query.where(Todo.created_at >= date_from)
        count_query = count_query.where(Todo.created_at >= date_from)
    if date_to is not None:
        query = query.where(Todo.created_at <= date_to)
        count_query = count_query.where(Todo.created_at <= date_to)

    # Pagination & sorting
    query = (
        query
        .order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    todos = list(result.scalars().all())

    total = await db.execute(count_query)
    total_count = total.scalar_one() or 0

    return todos, total_count


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    result = await db.execute(
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.id == todo_id)
    )
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    for key, value in update_data.items():
        setattr(todo, key, value)
    await db.flush()
    await db.refresh(todo)
    # Ensure tags remain available
    result = await db.execute(
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.id == todo.id)
    )
    return result.scalar_one()


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()
