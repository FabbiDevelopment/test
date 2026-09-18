import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import Tag, todo_tags
from app.models.todo import Todo
from app.schemas.todo import TodoCreate


async def create_todo(db: AsyncSession, todo_data: TodoCreate, user_id: uuid.UUID) -> Todo:
    todo = Todo(title=todo_data.title, description=todo_data.description, user_id=user_id)
    db.add(todo)
    await db.flush()
    await db.refresh(todo, attribute_names=["tags"])
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
    filters = [Todo.user_id == user_id]
    if status == "completed":
        filters.append(Todo.completed.is_(True))
    elif status == "active":
        filters.append(Todo.completed.is_(False))
    if keyword:
        term = f"%{keyword.strip()}%"
        filters.append(or_(Todo.title.ilike(term), Todo.description.ilike(term)))
    if date_from:
        filters.append(Todo.created_at >= date_from)
    if date_to:
        filters.append(Todo.created_at <= date_to)

    query = select(Todo).options(selectinload(Todo.tags)).where(*filters)
    count_query = select(func.count(Todo.id)).where(*filters)
    if tag_id:
        query = query.join(todo_tags).join(Tag).where(
            Tag.id == tag_id, Tag.user_id == user_id
        )
        count_query = count_query.join(todo_tags).join(Tag).where(
            Tag.id == tag_id, Tag.user_id == user_id
        )

    result = await db.execute(
        query.order_by(Todo.created_at.desc(), Todo.id.desc()).offset(skip).limit(limit)
    )
    total = await db.execute(count_query)
    return list(result.scalars().unique().all()), total.scalar_one()


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
    await db.refresh(todo, attribute_names=["tags"])
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()


async def bulk_update_status(
    db: AsyncSession, todo_ids: list[uuid.UUID], user_id: uuid.UUID, completed: bool
) -> list[Todo] | None:
    unique_ids = set(todo_ids)
    result = await db.execute(
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.id.in_(unique_ids), Todo.user_id == user_id)
    )
    todos = list(result.scalars().all())
    if len(todos) != len(unique_ids):
        return None
    for todo in todos:
        todo.completed = completed
    await db.flush()
    return todos