from datetime import datetime
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import (
    AttachTagRequest,
    BulkStatusUpdateRequest,
    BulkStatusUpdateResponse,
    TagResponse,
)
from app.schemas.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate
from app.services.tag_service import (
    attach_tag_to_todo,
    bulk_update_status,
    detach_tag_from_todo,
    get_tag_by_id,
)
from app.services.todo_service import (
    create_todo,
    delete_todo,
    get_todo_by_id,
    get_todos,
    update_todo,
)

router = APIRouter()

CACHE_TTL = 300  # 5 minutes


def _serialize_todo_response(todo, current_user_email: str) -> TodoResponse:
    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=current_user_email,
        tags=[
            TagResponse(
                id=t.id,
                user_id=t.user_id,
                name=t.name,
                color=t.color,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in getattr(todo, "tags", [])
        ],
    )


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    status_filter: str | None = Query(None, alias="status"),
    tag_id: uuid.UUID | None = Query(None),
    keyword: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated list of todos with optional advanced filters."""
    skip = (page - 1) * size

    cache_key = (
        f"todos:list:{current_user.id}:p:{page}:s:{size}:"
        f"st:{status_filter}:t:{tag_id}:kw:{keyword}:"
        f"df:{date_from.isoformat() if date_from else ''}:"
        f"dt:{date_to.isoformat() if date_to else ''}"
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
        status=status_filter,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )

    items = [_serialize_todo_response(todo, current_user.email) for todo in todos]

    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )

    # Cache the response
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
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return _serialize_todo_response(todo, current_user.email)


@router.patch("/bulk-status", response_model=BulkStatusUpdateResponse)
async def bulk_update_todos_status(
    payload: BulkStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Bulk update completed status for multiple todos in a single transaction."""
    updated_count = await bulk_update_status(
        db,
        user_id=current_user.id,
        todo_ids=payload.todo_ids,
        completed=payload.completed,
    )
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return BulkStatusUpdateResponse(updated_count=updated_count)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific todo by ID."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this todo",
        )

    return _serialize_todo_response(todo, current_user.email)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update a todo item."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this todo",
        )

    update_data = todo_data.model_dump(exclude_unset=True)

    if todo_data.completed is not None:
        todo.completed = todo_data.completed

    if "title" in update_data:
        todo.title = update_data["title"]
    if "description" in update_data:
        todo.description = update_data["description"]

    updated_todo = await update_todo(db, todo, {})
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return _serialize_todo_response(updated_todo, current_user.email)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a todo item."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this todo",
        )

    await delete_todo(db, todo)
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return None


@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag(
    todo_id: uuid.UUID,
    payload: AttachTagRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach an existing tag owned by user to a todo owned by user."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this todo",
        )

    tag = await get_tag_by_id(db, payload.tag_id, current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found or does not belong to user",
        )

    updated_todo = await attach_tag_to_todo(db, todo, tag)
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return _serialize_todo_response(updated_todo, current_user.email)


@router.delete("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
async def detach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Detach a tag from a todo item."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this todo",
        )

    updated_todo = await detach_tag_from_todo(db, todo, tag_id)
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return _serialize_todo_response(updated_todo, current_user.email)
