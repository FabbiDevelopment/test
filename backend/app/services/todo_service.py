import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

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
        tags=[],
    )
    db.add(todo)
    await db.flush()
    return todo


async def get_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    status: bool | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[Todo], int]:
    """Get a user's Todos with owner-scoped filters and stable pagination."""
    conditions = _todo_filter_conditions(
        user_id=user_id,
        status=status,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )
    query = (
        select(Todo)
        .options(joinedload(Todo.user), selectinload(Todo.tags))
        .where(*conditions)
        .order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    todos = list(result.scalars().all())

    count_query = select(func.count()).select_from(Todo).where(*conditions)
    total = await db.execute(count_query)

    return todos, total.scalar_one()


async def get_todo_by_id(
    db: AsyncSession,
    todo_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Todo | None:
    result = await db.execute(
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(
            Todo.id == todo_id,
            Todo.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    for key, value in update_data.items():
        setattr(todo, key, value)
    await db.flush()
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()


async def attach_tag_to_todo(
    db: AsyncSession, todo_id: uuid.UUID, tag_id: uuid.UUID
) -> None:
    await db.execute(todo_tags.insert().values(todo_id=todo_id, tag_id=tag_id))
    await db.flush()


async def detach_tag_from_todo(
    db: AsyncSession, todo_id: uuid.UUID, tag_id: uuid.UUID
) -> bool:
    result = await db.execute(
        delete(todo_tags).where(
            todo_tags.c.todo_id == todo_id,
            todo_tags.c.tag_id == tag_id,
        )
    )
    await db.flush()
    return result.rowcount == 1


async def bulk_update_todo_status(
    db: AsyncSession,
    todo_ids: list[uuid.UUID],
    user_id: uuid.UUID,
    completed: bool,
) -> list[Todo] | None:
    """Stage one all-or-nothing owner-scoped status update for commit by the caller."""
    result = await db.execute(
        select(Todo).where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
    )
    todos = list(result.scalars().all())
    if len(todos) != len(todo_ids):
        return None

    updated_at = datetime.now(timezone.utc)
    for todo in todos:
        todo.completed = completed
        todo.updated_at = updated_at
    await db.flush()
    return todos


def _todo_filter_conditions(
    *,
    user_id: uuid.UUID,
    status: bool | None,
    tag_id: uuid.UUID | None,
    keyword: str | None,
    date_from: date | None,
    date_to: date | None,
):
    conditions = [Todo.user_id == user_id]
    if status is not None:
        conditions.append(Todo.completed == status)
    if tag_id is not None:
        conditions.append(Todo.tags.any(and_(Tag.id == tag_id, Tag.user_id == user_id)))
    if keyword:
        search = f"%{keyword}%"
        conditions.append(or_(Todo.title.ilike(search), Todo.description.ilike(search)))
    if date_from is not None:
        conditions.append(Todo.created_at >= _start_of_day(date_from))
    if date_to is not None:
        conditions.append(Todo.created_at < _start_of_day(date_to + timedelta(days=1)))
    return conditions


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)
