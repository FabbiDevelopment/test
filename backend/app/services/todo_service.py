import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import todo_tags
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
    status: str | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Todo], int]:
    """Get all todos with pagination, filtering, and tag joins for a specific user."""
    base_conditions = [Todo.user_id == user_id]

    if status == "active":
        base_conditions.append(Todo.completed.is_(False))
    elif status == "completed":
        base_conditions.append(Todo.completed.is_(True))

    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        base_conditions.append(
            or_(Todo.title.ilike(kw), Todo.description.ilike(kw))
        )

    if date_from:
        base_conditions.append(Todo.created_at >= date_from)

    if date_to:
        base_conditions.append(Todo.created_at <= date_to)

    query = select(Todo).where(*base_conditions)

    if tag_id:
        query = query.join(todo_tags, todo_tags.c.todo_id == Todo.id).where(
            todo_tags.c.tag_id == tag_id
        )

    # Order by created_at DESC, id DESC as required by README
    query = query.order_by(Todo.created_at.desc(), Todo.id.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    todos = list(result.scalars().unique().all())

    # Count total
    count_query = select(func.count(Todo.id)).where(*base_conditions)
    if tag_id:
        count_query = count_query.join(todo_tags, todo_tags.c.todo_id == Todo.id).where(
            todo_tags.c.tag_id == tag_id
        )
    total_result = await db.execute(count_query)

    return todos, total_result.scalar_one()


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
