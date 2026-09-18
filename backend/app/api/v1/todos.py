import hashlib
import json
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TodoTagRequest
from app.schemas.todo import (
    TodoBulkStatusResponse,
    TodoBulkStatusUpdate,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.services.todo_service import (
    bulk_update_status,
    create_todo,
    delete_todo,
    get_todo_by_id,
    get_todos,
    update_todo,
)

router = APIRouter()
CACHE_TTL = 300


async def invalidate_todo_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    await redis.delete_pattern(f"todos:{user_id}:*")


def cache_key(user_id: uuid.UUID, **filters) -> str:
    serialized = json.dumps(filters, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode()).hexdigest()[:20]
    return f"todos:{user_id}:query:{digest}"


async def _owned_tag(db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID) -> Tag:
    tag = await db.scalar(select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id))
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.get("", response_model=TodoListResponse)
async def list_todos(
    status_filter: Literal["all", "active", "completed"] = Query("all", alias="status"),
    tag_id: uuid.UUID | None = None,
    keyword: str | None = Query(default=None, max_length=200),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be before date_to")
    if tag_id:
        await _owned_tag(db, tag_id, current_user.id)

    completed = None
    if status_filter == "active":
        completed = False
    elif status_filter == "completed":
        completed = True

    params = {
        "status": status_filter,
        "tag_id": tag_id,
        "keyword": keyword or None,
        "date_from": date_from,
        "date_to": date_to,
        "page": page,
        "page_size": page_size,
    }
    key = cache_key(current_user.id, **params)
    cached = await redis.get(key)
    if cached:
        return TodoListResponse(**json.loads(cached))

    todos, total = await get_todos(
        db,
        current_user.id,
        skip=(page - 1) * page_size,
        limit=page_size,
        completed=completed,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )
    response = TodoListResponse(
        items=[TodoResponse.model_validate(todo) for todo in todos],
        total=total,
        page=page,
        size=page_size,
    )
    await redis.set(key, response.model_dump_json(), ex=CACHE_TTL)
    return response


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await create_todo(db, todo_data, current_user.id)
    await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.patch("/bulk-status", response_model=TodoBulkStatusResponse)
async def update_bulk_status(
    payload: TodoBulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    updated = await bulk_update_status(
        db, payload.todo_ids, current_user.id, payload.completed
    )
    if updated == 0:
        raise HTTPException(status_code=404, detail="One or more todos not found")
    await invalidate_todo_cache(redis, current_user.id)
    return TodoBulkStatusResponse(updated=updated)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo = await update_todo(db, todo, todo_data)
    await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    await delete_todo(db, todo)
    await invalidate_todo_cache(redis, current_user.id)


@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag(
    todo_id: uuid.UUID,
    payload: TodoTagRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    tag = await _owned_tag(db, payload.tag_id, current_user.id)
    if all(existing.id != tag.id for existing in todo.tags):
        todo.tags.append(tag)
        await db.flush()
    await invalidate_todo_cache(redis, current_user.id)
    return await get_todo_by_id(db, todo.id, current_user.id)


@router.delete("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
async def detach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    tag = next((item for item in todo.tags if item.id == tag_id), None)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not attached")
    todo.tags.remove(tag)
    await db.flush()
    await invalidate_todo_cache(redis, current_user.id)
    return await get_todo_by_id(db, todo.id, current_user.id)
