import json
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.models.todo import Todo
from app.schemas.tag import TagResponse, AttachTagRequest
from app.schemas.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate, BulkStatusUpdate
from app.services.todo_service import (
    create_todo,
    delete_todo,
    get_todo_by_id,
    get_todos,
    update_todo,
    bulk_update_status,
)
from app.services.tag_service import (
    get_tag_by_id,
    get_todo_tag,
    attach_tag_to_todo,
    detach_tag_from_todo,
)

router = APIRouter()

CACHE_TTL = 300


def build_todo_response(todo: Todo, user_email: str) -> TodoResponse:
    tags: list[TagResponse] = []

    # Only access todo_tags if they are loaded (avoids lazy-load errors)
    from sqlalchemy import inspect
    inspected = inspect(todo)
    if "todo_tags" not in inspected.unloaded:
        tags = [TagResponse(
            id=tt.tag.id, name=tt.tag.name, color=tt.tag.color,
            created_at=tt.tag.created_at, updated_at=tt.tag.updated_at
        ) for tt in todo.todo_tags if tt.tag is not None]

    return TodoResponse(
        id=todo.id, title=todo.title, description=todo.description,
        completed=todo.completed, user_id=todo.user_id,
        created_at=todo.created_at, updated_at=todo.updated_at,
        user_email=user_email, tags=tags,
    )


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    status: bool | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    skip = (page - 1) * size

    # Adjust date_to to end of day if provided
    adjusted_date_to = date_to
    if date_to is not None:
        adjusted_date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)

    # build cache key considering filters
    cache_key = f"todos:{current_user.id}:page:{page}:size:{size}:status:{status}:tag:{tag_id}:kw:{keyword}:from:{date_from}:to:{adjusted_date_to}"

    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return TodoListResponse(**cached_data)

    todos, total = await get_todos(
        db, user_id=current_user.id, skip=skip, limit=size,
        status=status, tag_id=tag_id, keyword=keyword,
        date_from=date_from, date_to=adjusted_date_to
    )

    items = [build_todo_response(todo, current_user.email) for todo in todos]
    response = TodoListResponse(items=items, total=total, page=page, size=size)
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)
    return response


@router.patch("/bulk-status")
async def bulk_update_todo_status(
    payload: BulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    try:
        count = await bulk_update_status(db, current_user.id, payload.todo_ids, payload.completed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await redis.delete_pattern(f"todos:{current_user.id}:*")
    return {"updated_count": count}


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await create_todo(db, todo_data, current_user.id)
    await redis.delete_pattern(f"todos:{current_user.id}:*")
    return build_todo_response(todo, current_user.email)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return build_todo_response(todo, current_user.email)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    update_dict = todo_data.model_dump(exclude_unset=True)
    updated_todo = await update_todo(db, todo, update_dict)
    await redis.delete_pattern(f"todos:{current_user.id}:*")

    # Re-fetch to ensure tags are loaded after refresh
    refreshed = await get_todo_by_id(db, updated_todo.id)
    return build_todo_response(refreshed, current_user.email)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    await delete_todo(db, todo)
    await redis.delete_pattern(f"todos:{current_user.id}:*")
    return None


# --- Tag attachment endpoints (nested under /todos/{todo_id}/tags) ---

@router.post("/{todo_id}/tags", status_code=status.HTTP_201_CREATED)
async def attach_tag(
    todo_id: uuid.UUID,
    payload: AttachTagRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach a tag to a todo."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    tag = await get_tag_by_id(db, payload.tag_id)
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    # Check if already attached
    existing = await get_todo_tag(db, todo_id, payload.tag_id)
    if existing:
        raise HTTPException(status_code=400, detail="Tag already attached to this todo")

    await attach_tag_to_todo(db, todo_id, payload.tag_id)
    await redis.delete_pattern(f"todos:{current_user.id}:*")
    return {"message": "Tag attached"}


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Detach a tag from a todo."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    tag = await get_tag_by_id(db, tag_id)
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    await detach_tag_from_todo(db, todo_id, tag_id)
    await redis.delete_pattern(f"todos:{current_user.id}:*")
