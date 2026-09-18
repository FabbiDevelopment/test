import hashlib
import json
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagResponse
from app.schemas.todo import (
    TodoBulkStatusResult,
    TodoBulkStatusUpdate,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.services.tag_service import get_tag_by_id
from app.services.todo_service import (
    attach_tag,
    bulk_update_status,
    create_todo,
    delete_todo,
    detach_tag,
    get_todo_by_id,
    get_todos,
    update_todo,
)

router = APIRouter()

CACHE_TTL = 300  # 5 minutes


def _cache_key(
    user_id: uuid.UUID,
    page: int,
    size: int,
    status: str | None,
    tag_id: uuid.UUID | None,
    keyword: str | None,
    date_from: date | None,
    date_to: date | None,
) -> str:
    """Per-user, per-page, per-filter-combination cache key.

    All filter/query parameters are folded into the key (hashed, since
    keyword text could contain characters Redis keys shouldn't have) so
    two different filter combinations never collide on the same cached
    response, and so `_invalidate_list_cache`'s wildcard-by-user-id
    pattern still catches every cached variant for that user.
    """
    filters = f"{status}:{tag_id}:{keyword}:{date_from}:{date_to}"
    filters_hash = hashlib.sha1(filters.encode()).hexdigest()[:16]
    return f"todos:list:{user_id}:{page}:{size}:{filters_hash}"


async def _invalidate_list_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    """Drop every cached list page/filter-combo for this user after a write.

    In a real deployment prefer a Redis key pattern (SCAN + DELETE) over
    KEYS for very large keyspaces, or a version counter embedded in the
    key instead of pattern deletion.
    """
    keys = await redis.keys(f"todos:list:{user_id}:*")
    if keys:
        await redis.delete(*keys)


def _serialize_todo(todo) -> TodoResponse:
    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        tags=[TagResponse.model_validate(t) for t in todo.tags],
    )


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(
        None, alias="status", pattern="^(completed|active)$", description="Filter by completion status"
    ),
    tag_id: uuid.UUID | None = Query(None, description="Filter by attached tag"),
    keyword: str | None = Query(None, max_length=200, description="Search title/description"),
    date_from: date | None = Query(None, description="Only todos created on/after this date"),
    date_to: date | None = Query(None, description="Only todos created on/before this date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated, filterable list of the current user's todos."""
    skip = (page - 1) * size

    cache_key = _cache_key(
        current_user.id, page, size, status_filter, tag_id, keyword, date_from, date_to
    )

    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return TodoListResponse(**cached_data)

    todos, total = await get_todos(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=size,
        status=status_filter,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )

    response = TodoListResponse(
        items=[_serialize_todo(t) for t in todos],
        total=total,
        page=page,
        size=size,
    )

    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)

    return response


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Create a new todo item."""
    todo = await create_todo(db, todo_data, current_user.id)
    await _invalidate_list_cache(redis, current_user.id)
    return _serialize_todo(todo)


@router.patch("/bulk-status", response_model=TodoBulkStatusResult)
async def bulk_update_todo_status(
    payload: TodoBulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Bulk mark todos completed/active. Only affects todos the caller owns -
    IDs for other users' todos (or nonexistent IDs) come back in
    `skipped_ids` rather than causing an error, so a partially-valid
    selection still succeeds for the valid part.
    """
    updated_ids, skipped_ids = await bulk_update_status(
        db, current_user.id, payload.todo_ids, payload.completed
    )
    await _invalidate_list_cache(redis, current_user.id)
    return TodoBulkStatusResult(updated_ids=updated_ids, skipped_ids=skipped_ids)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific todo by ID. Scoped to the current user to prevent IDOR."""
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    return _serialize_todo(todo)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update a todo item. Scoped to the current user to prevent IDOR."""
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    update_data = todo_data.model_dump(exclude_unset=True)

    if update_data.get("completed") is not None:
        todo.completed = update_data["completed"]
    if update_data.get("title") is not None:
        todo.title = update_data["title"]
    if "description" in update_data:
        todo.description = update_data["description"]

    updated_todo = await update_todo(db, todo, {})
    await _invalidate_list_cache(redis, current_user.id)

    return _serialize_todo(updated_todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a todo item. Scoped to the current user to prevent IDOR."""
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    await delete_todo(db, todo)
    await _invalidate_list_cache(redis, current_user.id)

    return None


class TagAttachRequest(BaseModel):
    tag_id: uuid.UUID


@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag_to_todo(
    todo_id: uuid.UUID,
    payload: TagAttachRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach a tag to a todo. Both the todo and the tag must belong to the
    caller - a user can never attach someone else's tag, nor tag someone
    else's todo.
    """
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    tag = await get_tag_by_id(db, payload.tag_id, current_user.id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    updated_todo = await attach_tag(db, todo, tag)
    await _invalidate_list_cache(redis, current_user.id)

    return _serialize_todo(updated_todo)


@router.delete("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
async def detach_tag_from_todo(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Detach a tag from a todo. Scoped to the current user."""
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    updated_todo = await detach_tag(db, todo, tag_id)
    await _invalidate_list_cache(redis, current_user.id)

    return _serialize_todo(updated_todo)
