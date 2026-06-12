import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.todo import Todo
from app.models.tag import TodoTag
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
    await db.refresh(todo, ["tags"])
    return todo


async def get_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[Todo], int]:
    """Get all todos with pagination and filtering for a specific user."""
    query = select(Todo).where(Todo.user_id == user_id)

    if status == "completed":
        query = query.where(Todo.completed == True)
    elif status == "active":
        query = query.where(Todo.completed == False)

    if tag_id:
        query = query.join(TodoTag, Todo.id == TodoTag.todo_id).where(TodoTag.tag_id == tag_id)

    if keyword:
        query = query.where(Todo.title.ilike(f"%{keyword}%"))

    if date_from:
        try:
            df = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.where(Todo.created_at >= df)
        except ValueError:
            pass

    if date_to:
        try:
            dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.where(Todo.created_at <= dt)
        except ValueError:
            pass

    # Count total (before selectinload and order/limit)
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(count_query)

    query = query.options(selectinload(Todo.tags))
    query = query.order_by(Todo.created_at.desc(), Todo.id.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    todos = list(result.scalars().all())

    return todos, total.scalar_one()


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    result = await db.execute(select(Todo).options(selectinload(Todo.tags)).where(Todo.id == todo_id))
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    for key, value in update_data.items():
        setattr(todo, key, value)
    await db.flush()
    await db.refresh(todo, ["tags"])
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()
