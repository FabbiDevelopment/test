import hashlib
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagAttachRequest
from app.schemas.todo import BulkStatusRequest, TodoCreate, TodoListResponse, TodoResponse, TodoUpdate
from app.services.tag_service import get_tag
from app.services.todo_service import (
    bulk_update_status, create_todo, delete_todo, get_todo_by_id, get_todos, update_todo,
)

router = APIRouter()
CACHE_TTL = 300


def todo_cache_pattern(user_id: uuid.UUID) -> str:
    return f"todos:list:{user_id}:*"


async def invalidate_todo_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    await redis.delete_pattern(todo_cache_pattern(user_id))


def _cache_key(user_id: uuid.UUID, **params: object) -> str:
    normalized = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return f"todos:list:{user_id}:{digest}"


@router.get("", response_model=TodoListResponse)
async def list_todos(
    status_filter: str | None = Query(None, alias="status", pattern="^(active|completed|all)$"),
    tag_id: uuid.UUID | None = None,
    keyword: str | None = Query(None, max_length=200),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    size: int | None = Query(None, ge=1, le=100, include_in_schema=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    page_size = size or page_size
    params = dict(status=status_filter, tag_id=tag_id, keyword=keyword, date_from=date_from, date_to=date_to, page=page, page_size=page_size)
    has_filters = any([status_filter not in (None, "all"), tag_id, keyword, date_from, date_to])
    cache_key = (
        _cache_key(current_user.id, **params)
        if has_filters
        else f"todos:list:{current_user.id}:{page}:{page_size}"
    )
    cached = await redis.get(cache_key)
    if cached:
        return TodoListResponse(**json.loads(cached))

    todos, total = await get_todos(
        db, current_user.id, (page - 1) * page_size, page_size,
        status_filter, tag_id, keyword, date_from, date_to,
    )
    items = [
        TodoResponse.model_validate(todo).model_copy(update={"user_email": current_user.email})
        for todo in todos
    ]
    response = TodoListResponse(items=items, total=total, page=page, size=page_size)
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)
    return response


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(todo_data: TodoCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await create_todo(db, todo_data, current_user.id)
    await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.patch("/bulk-status", response_model=list[TodoResponse])
async def update_bulk_status(data: BulkStatusRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todos = await bulk_update_status(db, data.todo_ids, current_user.id, data.completed)
    if todos is None:
        raise HTTPException(status_code=404, detail="One or more todos not found")
    await invalidate_todo_cache(redis, current_user.id)
    return todos


@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag(todo_id: uuid.UUID, data: TagAttachRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    tag = await get_tag(db, data.tag_id, current_user.id)
    if not todo or not tag:
        raise HTTPException(status_code=404, detail="Todo or tag not found")
    if all(existing.id != tag.id for existing in todo.tags):
        todo.tags.append(tag)
        await db.flush()
    await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.delete("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
async def detach_tag(todo_id: uuid.UUID, tag_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    tag = next((item for item in todo.tags if item.id == tag_id), None)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not attached")
    todo.tags.remove(tag)
    await db.flush()
    await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(todo_id: uuid.UUID, todo_data: TodoUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    updated = await update_todo(db, todo, todo_data.model_dump(exclude_unset=True))
    await invalidate_todo_cache(redis, current_user.id)
    return updated


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(todo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    await delete_todo(db, todo)
    await invalidate_todo_cache(redis, current_user.id)