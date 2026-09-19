import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagResponse
from app.schemas.todo import (
    BulkStatusUpdate,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.services.tag_service import get_tag_by_id
from app.services.todo_service import (
    attach_tag_to_todo,
    bulk_update_status,
    create_todo,
    delete_todo,
    detach_tag_from_todo,
    get_todo_by_id,
    get_todos,
    update_todo,
)

router = APIRouter()

CACHE_TTL = 300  # 5 minutes


def _to_todo_response(todo, user_email: str | None = None) -> TodoResponse:
    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=user_email,
        tags=[
            TagResponse(
                id=tag.id,
                user_id=tag.user_id,
                name=tag.name,
                color=tag.color,
                created_at=tag.created_at,
                updated_at=tag.updated_at,
            )
            for tag in (getattr(todo, "tags", []) or [])
        ],
    )


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    page_size: int | None = Query(None, ge=1),
    status: str | None = Query(None),
    tag_id: uuid.UUID | None = Query(None),
    keyword: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated list of todos with optional filters."""
    limit = page_size if page_size is not None else size
    skip = (page - 1) * limit

    cache_key = (
        f"todos:user:{current_user.id}:p:{page}:s:{limit}:st:{status}:t:{tag_id}:"
        f"k:{keyword}:df:{date_from}:dt:{date_to}"
    )

    # Try cache
    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return TodoListResponse(**cached_data)

    todos, total = await get_todos(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status_filter=status,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )

    items = [_to_todo_response(todo, current_user.email) for todo in todos]

    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        size=limit,
    )

    # Cache response
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
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")
    return _to_todo_response(todo, current_user.email)


@router.patch("/bulk-status")
async def bulk_status(
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
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")
    return {"updated_count": updated_count, "completed": payload.completed}


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific todo by ID."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    return _to_todo_response(todo, current_user.email)


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
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    update_data = todo_data.model_dump(exclude_unset=True)
    updated_todo = await update_todo(db, todo, update_data)
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")

    return _to_todo_response(updated_todo, current_user.email)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a todo item."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    await delete_todo(db, todo)
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")
    return None


@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach a user-owned tag to a user-owned todo."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    updated_todo = await attach_tag_to_todo(db, todo, tag)
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")
    return _to_todo_response(updated_todo, current_user.email)


@router.delete("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
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

    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    updated_todo = await detach_tag_from_todo(db, todo, tag)
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")
    return _to_todo_response(updated_todo, current_user.email)
