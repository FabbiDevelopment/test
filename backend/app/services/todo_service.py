import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    return await get_todo_by_id(db, todo.id)


from datetime import datetime
from sqlalchemy.orm import selectinload
from app.models.todo_tag import TodoTag

async def get_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    status: bool | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Todo], int]:
    """Get all todos with pagination and filters for a specific user."""
    base_query = select(Todo).where(Todo.user_id == user_id)
    
    if status is not None:
        base_query = base_query.where(Todo.completed == status)
    
    if keyword:
        base_query = base_query.where(
            Todo.title.ilike(f"%{keyword}%") | Todo.description.ilike(f"%{keyword}%")
        )
        
    if date_from:
        base_query = base_query.where(Todo.created_at >= date_from)
        
    if date_to:
        base_query = base_query.where(Todo.created_at <= date_to)
        
    if tag_id:
        base_query = base_query.join(TodoTag, TodoTag.todo_id == Todo.id).where(TodoTag.tag_id == tag_id)

    # Order by created_at DESC, id DESC as requested
    base_query = base_query.order_by(Todo.created_at.desc(), Todo.id.desc())

    # Fetch data
    query = base_query.offset(skip).limit(limit).options(selectinload(Todo.tags))
    result = await db.execute(query)
    todos = list(result.scalars().all())

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total = await db.execute(count_query)

    return todos, total.scalar_one()


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    result = await db.execute(select(Todo).options(selectinload(Todo.tags)).where(Todo.id == todo_id))
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
