import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
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
    status_filter: str | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Todo], int]:
    """Get all todos with filtering and pagination for a specific user."""
    query = select(Todo).where(Todo.user_id == user_id)

    if status_filter == "completed":
        query = query.where(Todo.completed.is_(True))
    elif status_filter == "active":
        query = query.where(Todo.completed.is_(False))

    if tag_id:
        query = query.join(Todo.tags).where(Tag.id == tag_id)

    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(
            or_(
                Todo.title.ilike(pattern),
                Todo.description.ilike(pattern),
            )
        )

    if date_from:
        query = query.where(Todo.created_at >= date_from)

    if date_to:
        query = query.where(Todo.created_at <= date_to)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar_one()

    # Order by created_at DESC, id DESC
    query = query.order_by(Todo.created_at.desc(), Todo.id.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    todos = list(result.scalars().unique().all())

    return todos, total


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    result = await db.execute(select(Todo).where(Todo.id == todo_id))
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
