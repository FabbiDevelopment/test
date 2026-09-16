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
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Todo], int]:
    """Get all todos with pagination for a specific user."""
    query = select(Todo).where(Todo.user_id == user_id)
    count_query = select(func.count()).select_from(Todo).where(Todo.user_id == user_id)

    if tag_id is not None:
        query = query.join(Todo.todo_tags).where(TodoTag.tag_id == tag_id)
        count_query = count_query.join(Todo.todo_tags).where(TodoTag.tag_id == tag_id)
    
    if status is not None:
        query = query.where(Todo.completed == status)
        count_query = count_query.where(Todo.completed == status)
        
    if keyword is not None:
        query = query.where((Todo.title.ilike(f"%{keyword}%")) | (Todo.description.ilike(f"%{keyword}%")))
        count_query = count_query.where((Todo.title.ilike(f"%{keyword}%")) | (Todo.description.ilike(f"%{keyword}%")))
        
    if date_from is not None:
        query = query.where(Todo.created_at >= date_from)
        count_query = count_query.where(Todo.created_at >= date_from)
        
    if date_to is not None:
        query = query.where(Todo.created_at <= date_to)
        count_query = count_query.where(Todo.created_at <= date_to)

    query = query.order_by(Todo.created_at.desc(), Todo.id.desc()).offset(skip).limit(limit)
    query = query.options(selectinload(Todo.todo_tags).selectinload(TodoTag.tag))
    
    result = await db.execute(query)
    todos = list(result.scalars().all())

    total = await db.execute(count_query)

    return todos, total.scalar_one()


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    result = await db.execute(
        select(Todo)
        .where(Todo.id == todo_id)
        .options(selectinload(Todo.todo_tags).selectinload(TodoTag.tag))
    )
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
    query = select(Todo).where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
    result = await db.execute(query)
    todos = list(result.scalars().all())
    if len(todos) != len(todo_ids):
        raise ValueError("Some todos not found or don't belong to user")
    for todo in todos:
        todo.completed = completed
    await db.flush()
    return len(todos)
