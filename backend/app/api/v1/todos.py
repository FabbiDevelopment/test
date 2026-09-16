from datetime import date
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagAttachRequest, TagResponse
from app.schemas.todo import (
    BulkStatusRequest,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.services.tag_service import (
    attach_tag_to_todo,
    detach_tag_from_todo,
    get_tag_by_id,
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

CACHE_TTL = 300  # 5 minutes


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int | None = Query(None, ge=1),
    page_size: int | None = Query(None, ge=1),
    status: bool | None = Query(None),
    tag_id: uuid.UUID | None = Query(None),
    keyword: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated and filtered list of todos for the current user."""
    effective_size = page_size if page_size is not None else (size if size is not None else 20)
    skip = (page - 1) * effective_size

    # Cache key covers all query and filter parameters
    cache_key = (
        f"todos:user:{current_user.id}:page:{page}:size:{effective_size}:"
        f"st:{status}:tag:{tag_id}:kw:{keyword or ''}:from:{date_from}:to:{date_to}"
    )

    # Try to get from cache
    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return TodoListResponse(**cached_data)

    todos, total = await get_todos(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=effective_size,
        status=status,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )

    items = [
        TodoResponse(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            completed=todo.completed,
            user_id=todo.user_id,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
            user_email=current_user.email,
            tags=[
                TagResponse(
                    id=t.id,
                    name=t.name,
                    color=t.color,
                    user_id=t.user_id,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in todo.tags
            ],
        )
        for todo in todos
    ]

    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        size=effective_size,
    )

    # Cache the response scoped to this user and query parameters
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)

    return response


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Create a new todo item and invalidate user's cached todo list."""
    todo = await create_todo(db, todo_data, current_user.id)
    todo.user_email = current_user.email

    # Invalidate user-scoped todo list cache
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")

    return todo


@router.patch("/bulk-status")
async def bulk_update_todo_status(
    bulk_data: BulkStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Bulk update status for todos belonging to current user."""
    updated_count = await bulk_update_status(
        db,
        todo_ids=bulk_data.todo_ids,
        completed=bulk_data.completed,
        user_id=current_user.id,
    )

    # Invalidate user-scoped todo list cache
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")

    return {"updated_count": updated_count}


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific todo by ID ensuring the current user owns it."""
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

    todo.user_email = current_user.email
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update a todo item verifying ownership and preserving unset fields."""
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
    updated_todo = await update_todo(db, todo, update_data)
    updated_todo.user_email = current_user.email

    # Invalidate user-scoped todo list cache
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")

    return updated_todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a todo item verifying ownership and invalidating user's cache."""
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

    # Invalidate user-scoped todo list cache
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")

    return None


@router.post("/{todo_id}/tags", status_code=status.HTTP_200_OK)
async def attach_tag(
    todo_id: uuid.UUID,
    payload: TagAttachRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach a tag to a todo item."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this todo",
        )

    tag = await get_tag_by_id(db, payload.tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    if tag.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot attach a tag belonging to another user",
        )

    await attach_tag_to_todo(db, todo, tag)
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")
    return {"message": "Tag attached successfully"}


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
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
            detail="Not authorized to modify this todo",
        )

    tag = await get_tag_by_id(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    if tag.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot detach a tag belonging to another user",
        )

    await detach_tag_from_todo(db, todo, tag)
    await redis.delete_pattern(f"todos:user:{current_user.id}:*")
    return {"message": "Tag detached successfully"}
