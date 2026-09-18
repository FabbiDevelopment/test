import uuid
from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import todo_tags
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate


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
    return await get_todo_by_id(db, todo.id, user_id)


def _todo_filters(
    user_id: uuid.UUID,
    completed: bool | None,
    tag_id: uuid.UUID | None,
    keyword: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
):
    filters = [Todo.user_id == user_id]
    if completed is not None:
        filters.append(Todo.completed == completed)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        filters.append(or_(Todo.title.ilike(pattern), Todo.description.ilike(pattern)))
    if date_from:
        filters.append(Todo.created_at >= date_from)
    if date_to:
        filters.append(Todo.created_at <= date_to)
    if tag_id:
        filters.append(
            Todo.id.in_(select(todo_tags.c.todo_id).where(todo_tags.c.tag_id == tag_id))
        )
    return filters


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
    filters = _todo_filters(user_id, completed, tag_id, keyword, date_from, date_to)
    query = (
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(*filters)
        .order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )
    todos = list((await db.execute(query)).scalars().all())
    total = await db.scalar(select(func.count()).select_from(Todo).where(*filters))
    return todos, total or 0


async def get_todo_by_id(
    db: AsyncSession, todo_id: uuid.UUID, user_id: uuid.UUID
) -> Todo | None:
    result = await db.execute(
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.id == todo_id, Todo.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, todo_data: TodoUpdate) -> Todo:
    for key, value in todo_data.model_dump(exclude_unset=True).items():
        setattr(todo, key, value)
    await db.flush()
    return await get_todo_by_id(db, todo.id, todo.user_id)


async def bulk_update_status(
    db: AsyncSession,
    todo_ids: list[uuid.UUID],
    user_id: uuid.UUID,
    completed: bool,
) -> int:
    unique_ids = set(todo_ids)
    owned_count = await db.scalar(
        select(func.count())
        .select_from(Todo)
        .where(Todo.id.in_(unique_ids), Todo.user_id == user_id)
    )
    if owned_count != len(unique_ids):
        return 0
    result = await db.execute(
        update(Todo)
        .where(Todo.id.in_(unique_ids), Todo.user_id == user_id)
        .values(completed=completed)
    )
    await db.flush()
    return result.rowcount or 0


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()
