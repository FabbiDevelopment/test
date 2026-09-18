import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.todo import Todo
from app.models.tag import Tag, TodoTag
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
    completed: bool | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Todo], int]:
    """Get a user's filtered todos with deterministic pagination."""
    filters = [Todo.user_id == user_id]
    if completed is not None:
        filters.append(Todo.completed == completed)
    if keyword:
        filters.append(Todo.title.ilike(f"%{keyword}%"))
    if date_from:
        filters.append(Todo.created_at >= date_from)
    if date_to:
        filters.append(Todo.created_at <= date_to)

    query = select(Todo).where(*filters)
    count_query = select(func.count()).select_from(Todo).where(*filters)
    if tag_id:
        tag_filter = TodoTag.tag_id == tag_id
        query = query.join(TodoTag).where(tag_filter)
        count_query = count_query.join(TodoTag).where(tag_filter)

    query = (
        query.options(selectinload(Todo.tag_links).selectinload(TodoTag.tag))
        .order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    todos = list(result.scalars().all())

    total = await db.execute(count_query)

    return todos, total.scalar_one()


async def get_todo_by_id(
    db: AsyncSession,
    todo_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Todo | None:
    result = await db.execute(
        select(Todo).options(
            selectinload(Todo.tag_links).selectinload(TodoTag.tag)
        ).where(
            Todo.id == todo_id,
            Todo.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_tag_by_id(db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID) -> Tag | None:
    result = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id))
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
