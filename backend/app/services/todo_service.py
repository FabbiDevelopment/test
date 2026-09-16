import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import func, or_, select, update
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
    status: bool | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: date | datetime | None = None,
    date_to: date | datetime | None = None,
) -> tuple[list[Todo], int]:
    """Get todos with filtering, ordered by created_at DESC, id DESC."""
    query = select(Todo).where(Todo.user_id == user_id)
    count_query = select(func.count(Todo.id)).where(Todo.user_id == user_id)

    if status is not None:
        query = query.where(Todo.completed == status)
        count_query = count_query.where(Todo.completed == status)

    if tag_id is not None:
        tag_condition = Todo.tags.any(Tag.id == tag_id)
        query = query.where(tag_condition)
        count_query = count_query.where(tag_condition)

    if keyword:
        term = f"%{keyword.strip()}%"
        kw_condition = or_(
            Todo.title.ilike(term),
            Todo.description.ilike(term),
        )
        query = query.where(kw_condition)
        count_query = count_query.where(kw_condition)

    if date_from is not None:
        if isinstance(date_from, datetime):
            dt_from = date_from
        else:
            dt_from = datetime.combine(date_from, time.min).replace(tzinfo=timezone.utc)
        query = query.where(Todo.created_at >= dt_from)
        count_query = count_query.where(Todo.created_at >= dt_from)

    if date_to is not None:
        if isinstance(date_to, datetime):
            dt_to = date_to
        else:
            dt_to = datetime.combine(date_to, time.max).replace(tzinfo=timezone.utc)
        query = query.where(Todo.created_at <= dt_to)
        count_query = count_query.where(Todo.created_at <= dt_to)

    # Order by created_at DESC, id DESC
    query = query.order_by(Todo.created_at.desc(), Todo.id.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    todos = list(result.scalars().all())

    total = await db.execute(count_query)
    return todos, total.scalar_one()


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


async def bulk_update_status(
    db: AsyncSession,
    todo_ids: list[uuid.UUID],
    completed: bool,
    user_id: uuid.UUID,
) -> int:
    """Bulk update completion status for todos belonging to the user."""
    stmt = (
        update(Todo)
        .where(
            Todo.id.in_(todo_ids),
            Todo.user_id == user_id,
        )
        .values(
            completed=completed,
            updated_at=datetime.now(timezone.utc),
        )
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount
