import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    """Get todos with filters — Level 4."""
    base = select(Todo).where(Todo.user_id == user_id)

    if completed is not None:
        base = base.where(Todo.completed == completed)

    if tag_id is not None:
        base = base.join(TodoTag, TodoTag.todo_id == Todo.id).where(
            TodoTag.tag_id == tag_id
        )

    if keyword:
        pattern = f"%{keyword}%"
        base = base.where(
            or_(Todo.title.ilike(pattern), Todo.description.ilike(pattern))
        )

    if date_from is not None:
        base = base.where(Todo.created_at >= date_from)
    if date_to is not None:
        base = base.where(Todo.created_at <= date_to)

    # SAI (cũ): không ORDER BY — pagination không ổn định
    # THÊM: created_at DESC, id DESC — khớp spec Level 4 + index
    query = (
        base.order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    todos = list(result.scalars().unique().all())

    count_query = select(func.count(func.distinct(Todo.id))).select_from(Todo).where(
        Todo.user_id == user_id
    )
    if completed is not None:
        count_query = count_query.where(Todo.completed == completed)
    if tag_id is not None:
        count_query = count_query.join(TodoTag, TodoTag.todo_id == Todo.id).where(
            TodoTag.tag_id == tag_id
        )
    if keyword:
        pattern = f"%{keyword}%"
        count_query = count_query.where(
            or_(Todo.title.ilike(pattern), Todo.description.ilike(pattern))
        )
    if date_from is not None:
        count_query = count_query.where(Todo.created_at >= date_from)
    if date_to is not None:
        count_query = count_query.where(Todo.created_at <= date_to)

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
    user_id: uuid.UUID,
    todo_ids: list[uuid.UUID],
    completed: bool,
) -> int:
    # THÊM: bulk update trong cùng session/transaction — Level 4
    result = await db.execute(
        select(Todo).where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
    )
    todos = list(result.scalars().all())
    for todo in todos:
        todo.completed = completed
    await db.flush()
    return len(todos)
