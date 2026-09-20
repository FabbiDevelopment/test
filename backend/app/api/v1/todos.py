from datetime import datetime
import json
import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.todo import Todo
from app.models.user import User
from app.schemas.tag import TagSimpleResponse
from app.schemas.todo import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkStatusUpdate,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.services.tag_service import (
    attach_tag_to_todo,
    detach_tag_from_todo,
    get_tag_by_id_and_user,
    get_tags_for_todo,
)
from app.services.todo_service import (
    bulk_delete_todos,
    bulk_update_status,
    create_todo,
    delete_todo,
    get_todo_by_id_and_user,
    get_todos,
    update_todo,
)

router = APIRouter()

CACHE_TTL_DEFAULT = 300  # 5 minutes for general listings
CACHE_TTL_KEYWORD = 60   # 1 minute for keyword search to prevent memory bloat


def to_todo_response(
    todo: Todo,
    user_email: str | None = None,
    tags: list[TagSimpleResponse] | None = None,
) -> TodoResponse:
    """Helper to convert Todo model to TodoResponse schema avoiding duplication and redundant queries."""
    tag_list = tags if tags is not None else [
        TagSimpleResponse.model_validate(t) for t in (todo.tags or [])
    ]
    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=user_email,
        tags=tag_list,
    )



async def delete_user_todos_cache(redis: RedisClient, user_id: uuid.UUID):
    """Invalidate all cached todo lists for a specific user."""
    if redis.client:
        keys = await redis.client.keys(f"todos:user:{user_id}:*")
        if keys:
            await redis.client.delete(*keys)



class AttachTagRequest(BaseModel):
    tag_id: uuid.UUID


@router.get("", response_model=TodoListResponse)
async def list_todos(
    status: bool | None = Query(None, description="Filter by completed status"),
    tag_id: uuid.UUID | None = Query(None, description="Filter by tag ID"),
    keyword: str | None = Query(None, description="Search keyword in title/description"),
    date_from: datetime | None = Query(None, description="Filter created_at from"),
    date_to: datetime | None = Query(None, description="Filter created_at to"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated list of todos with multi-criteria filtering."""
    skip = (page - 1) * size

    # Normalized canonical cache key
    clean_kw = keyword.strip().lower() if (keyword and keyword.strip()) else None
    cache_key = (
        f"todos:user:{current_user.id}:"
        f"st:{status}:tag:{tag_id}:kw:{clean_kw}:"
        f"df:{date_from}:dt:{date_to}:p:{page}:s:{size}"
    )

    # Try to get from cache
    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return TodoListResponse(**cached_data)

    todos, total = await get_todos(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=size,
        status=status,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )

    items = [to_todo_response(todo, current_user.email) for todo in todos]

    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )

    ttl = CACHE_TTL_KEYWORD if clean_kw else CACHE_TTL_DEFAULT
    await redis.set(cache_key, response.model_dump_json(), ex=ttl)

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
    await delete_user_todos_cache(redis, current_user.id)
    return to_todo_response(todo, current_user.email, tags=[])


@router.patch("/bulk-status")
async def bulk_update_todo_status(
    payload: BulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Bulk update completed status for multiple todos in a database transaction."""
    updated_count = await bulk_update_status(
        db,
        user_id=current_user.id,
        todo_ids=payload.todo_ids,
        completed=payload.completed,
    )
    await delete_user_todos_cache(redis, current_user.id)
    return {"updated_count": updated_count, "completed": payload.completed}


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
@router.delete("/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_existing_todos(
    payload: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Bulk delete multiple todos belonging to current user in a database transaction."""
    deleted_count = await bulk_delete_todos(
        db,
        user_id=current_user.id,
        todo_ids=payload.todo_ids,
    )
    await delete_user_todos_cache(redis, current_user.id)
    return {"deleted_count": deleted_count}



@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific todo by ID."""
    todo = await get_todo_by_id_and_user(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    return to_todo_response(todo, current_user.email)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update a todo item."""
    todo = await get_todo_by_id_and_user(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    update_data = todo_data.model_dump(exclude_unset=True)
    updated_todo = await update_todo(db, todo, update_data)
    await delete_user_todos_cache(redis, current_user.id)

    return to_todo_response(updated_todo, current_user.email)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a todo item."""
    todo = await get_todo_by_id_and_user(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    await delete_todo(db, todo)
    await delete_user_todos_cache(redis, current_user.id)
    return None


@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag(
    todo_id: uuid.UUID,
    payload: AttachTagRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach a tag to a todo item with ownership verification."""
    todo = await get_todo_by_id_and_user(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    tag = await get_tag_by_id_and_user(db, payload.tag_id, current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    await attach_tag_to_todo(db, todo, tag)
    await delete_user_todos_cache(redis, current_user.id)

    # Column-projected query: SELECT tags.id, tags.name, tags.color only
    tags = await get_tags_for_todo(db, todo.id)
    return to_todo_response(todo, current_user.email, tags=tags)




@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Detach a tag from a todo item with ownership verification."""
    todo = await get_todo_by_id_and_user(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    tag = await get_tag_by_id_and_user(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    await detach_tag_from_todo(db, todo, tag)
    await delete_user_todos_cache(redis, current_user.id)
    return None
