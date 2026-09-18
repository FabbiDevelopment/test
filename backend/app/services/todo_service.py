import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import TodoTag
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoResponse

TAG_LOAD = selectinload(Todo.todo_tags).selectinload(TodoTag.tag)


def todo_response(todo: Todo, user_email: str) -> TodoResponse:
    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=user_email,
        tags=sorted(
            [link.tag for link in todo.todo_tags], key=lambda tag: tag.name.lower()
        ),
    )


async def create_todo(
    db: AsyncSession, todo_data: TodoCreate, user_id: uuid.UUID
) -> Todo:
    todo = Todo(**todo_data.model_dump(), user_id=user_id, todo_tags=[])
    db.add(todo)
    await db.flush()
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
    query = select(Todo).where(Todo.user_id == user_id)
    if completed is not None:
        query = query.where(Todo.completed == completed)
    if tag_id is not None:
        query = query.where(
            Todo.id.in_(select(TodoTag.todo_id).where(TodoTag.tag_id == tag_id))
        )
    if keyword:
        # Search is literal: '%' and '_' in user input are not SQL wildcards.
        query = query.where(Todo.title.icontains(keyword, autoescape=True))
    if date_from:
        query = query.where(Todo.created_at >= date_from)
    if date_to:
        query = query.where(Todo.created_at <= date_to)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.scalars(
        query.options(TAG_LOAD)
        .order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.all()), total


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    return await db.scalar(select(Todo).where(Todo.id == todo_id).options(TAG_LOAD))


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    for key, value in update_data.items():
        setattr(todo, key, value)
    await db.flush()
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()
