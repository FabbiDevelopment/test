import uuid
from datetime import datetime
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import Tag, todo_tags
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
    await db.refresh(todo, attribute_names=["tags"])
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
    """Get todos with optional filters and pagination for a specific user."""
    query = (
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.user_id == user_id)
    )
    count_query = select(func.count(Todo.id)).where(Todo.user_id == user_id)

    # Filter by status
    if status_filter == "completed":
        query = query.where(Todo.completed.is_(True))
        count_query = count_query.where(Todo.completed.is_(True))
    elif status_filter in ("active", "incomplete"):
        query = query.where(Todo.completed.is_(False))
        count_query = count_query.where(Todo.completed.is_(False))

    # Filter by tag
    if tag_id:
        query = query.join(Todo.tags).where(Tag.id == tag_id)
        count_query = count_query.join(Todo.tags).where(Tag.id == tag_id)

    # Filter by keyword
    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(
            (Todo.title.ilike(pattern)) | (Todo.description.ilike(pattern))
        )
        count_query = count_query.where(
            (Todo.title.ilike(pattern)) | (Todo.description.ilike(pattern))
        )

    # Filter by date range
    if date_from:
        query = query.where(Todo.created_at >= date_from)
        count_query = count_query.where(Todo.created_at >= date_from)
    if date_to:
        query = query.where(Todo.created_at <= date_to)
        count_query = count_query.where(Todo.created_at <= date_to)

    # Apply ordering and pagination
    query = (
        query.order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    todos = list(result.scalars().all())

    total = await db.execute(count_query)
    total_count = total.scalar_one()

    return todos, total_count


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    query = (
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.id == todo_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    for key, value in update_data.items():
        setattr(todo, key, value)
    await db.flush()
    await db.refresh(todo, attribute_names=["tags"])
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()


async def attach_tag_to_todo(
    db: AsyncSession, todo: Todo, tag: Tag
) -> Todo:
    """Attach a tag to a todo if not already attached."""
    if tag not in todo.tags:
        todo.tags.append(tag)
        await db.flush()
        await db.refresh(todo, attribute_names=["tags"])
    return todo


async def detach_tag_from_todo(
    db: AsyncSession, todo: Todo, tag: Tag
) -> Todo:
    """Detach a tag from a todo."""
    if tag in todo.tags:
        todo.tags.remove(tag)
        await db.flush()
        await db.refresh(todo, attribute_names=["tags"])
    return todo


async def bulk_update_status(
    db: AsyncSession, user_id: uuid.UUID, todo_ids: list[uuid.UUID], completed: bool
) -> int:
    """Bulk update completed status in a transaction for owned todos."""
    query = (
        select(Todo)
        .where(Todo.user_id == user_id, Todo.id.in_(todo_ids))
    )
    result = await db.execute(query)
    todos = list(result.scalars().all())

    for t in todos:
        t.completed = completed

    await db.flush()
    return len(todos)
