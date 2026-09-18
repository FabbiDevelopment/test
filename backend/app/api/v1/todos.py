import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.tag import TodoTag
from app.models.todo import Todo
from app.models.user import User
from app.schemas.todo import BulkStatusUpdate, TagAttach, TodoCreate, TodoListResponse, TodoResponse, TodoUpdate
from app.schemas.tag import TagResponse
from app.services.todo_service import create_todo, delete_todo, get_tag_by_id, get_todo_by_id, get_todos, update_todo

router = APIRouter()
CACHE_TTL = 300


def serialize_todo(todo: Todo, user_email: str | None = None) -> TodoResponse:
    return TodoResponse(
        id=todo.id, title=todo.title, description=todo.description, completed=todo.completed,
        user_id=todo.user_id, created_at=todo.created_at, updated_at=todo.updated_at,
        user_email=user_email, tags=[TagResponse.model_validate(link.tag) for link in todo.tag_links],
    )


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=10000),
    completed: bool | None = None, tag_id: uuid.UUID | None = None,
    keyword: str | None = Query(None, min_length=1, max_length=200),
    date_from: datetime | None = None, date_to: datetime | None = None,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be before date_to")
    values = {"page": page, "size": size, "completed": completed, "tag_id": str(tag_id) if tag_id else None, "keyword": keyword, "date_from": date_from.isoformat() if date_from else None, "date_to": date_to.isoformat() if date_to else None}
    cache_key = f"todos:list:{current_user.id}:{json.dumps(values, sort_keys=True, separators=(',', ':'))}"
    cached = await redis.get(cache_key)
    if cached:
        return TodoListResponse(**json.loads(cached))
    todos, total = await get_todos(db, current_user.id, (page - 1) * size, size, completed, tag_id, keyword, date_from, date_to)
    response = TodoListResponse(items=[serialize_todo(todo, current_user.email) for todo in todos], total=total, page=page, size=size)
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)
    return response


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(todo_data: TodoCreate, redis: RedisClient = Depends(get_redis), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    todo = await create_todo(db, todo_data, current_user.id)
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return serialize_todo(todo, current_user.email)


@router.patch("/bulk-status", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_update_status(data: BulkStatusUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo_ids = list(set(data.todo_ids))
    result = await db.execute(select(Todo).where(Todo.id.in_(todo_ids), Todo.user_id == current_user.id))
    todos = list(result.scalars().all())
    if len(todos) != len(todo_ids):
        raise HTTPException(status_code=404, detail="One or more todos not found")
    for todo in todos:
        todo.completed = data.completed
    await db.flush()
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return None


@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag(todo_id: uuid.UUID, payload: TagAttach, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    tag = await get_tag_by_id(db, payload.tag_id, current_user.id)
    if not todo or not tag:
        raise HTTPException(status_code=404, detail="Todo or tag not found")
    exists = await db.execute(select(TodoTag).where(TodoTag.todo_id == todo_id, TodoTag.tag_id == payload.tag_id))
    if exists.scalar_one_or_none() is None:
        db.add(TodoTag(todo_id=todo_id, tag_id=payload.tag_id))
        await db.flush()
    db.expire(todo, ["tag_links"])
    refreshed = await get_todo_by_id(db, todo_id, current_user.id)
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return serialize_todo(refreshed, current_user.email)


@router.delete("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
async def detach_tag(todo_id: uuid.UUID, tag_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not todo or not tag:
        raise HTTPException(status_code=404, detail="Todo or tag not found")
    result = await db.execute(select(TodoTag).where(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Tag is not attached to this todo")
    await db.delete(link)
    await db.flush()
    db.expire(todo, ["tag_links"])
    refreshed = await get_todo_by_id(db, todo_id, current_user.id)
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return serialize_todo(refreshed, current_user.email)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return serialize_todo(todo, current_user.email)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(todo_id: uuid.UUID, todo_data: TodoUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    for key, value in todo_data.model_dump(exclude_unset=True).items():
        setattr(todo, key, value)
    updated = await update_todo(db, todo, {})
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return serialize_todo(updated, current_user.email)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(todo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    await delete_todo(db, todo)
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return None
