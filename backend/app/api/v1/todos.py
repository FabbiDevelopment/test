import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.tag import Tag, todo_tags
from app.models.todo import Todo
from app.models.user import User
from app.schemas.tag import BulkStatusUpdate, TagResponse
from app.schemas.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate
from app.services.todo_service import (
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
    """Get paginated list of todos with multi-parameter filtering."""
    skip = (page - 1) * size

    # Scope cache key per user + all filter parameters
    cache_key = f"todos:list:{current_user.id}:{status_filter}:{tag_id}:{keyword}:{date_from}:{date_to}:{page}:{size}"

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

    items = []
    for todo in todos:
        items.append(
            TodoResponse(
                id=todo.id,
                title=todo.title,
                description=todo.description,
                completed=todo.completed,
                user_id=todo.user_id,
                created_at=todo.created_at,
                updated_at=todo.updated_at,
                user_email=current_user.email,
                tags=[TagResponse.model_validate(t) for t in todo.tags],
            )
        )

    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
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

    # Invalidate user todo list cache
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=current_user.email,
        tags=[],
    )


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

    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=current_user.email,
        tags=[TagResponse.model_validate(t) for t in todo.tags],
    )


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
            detail="Not authorized to update this todo",
        )

    update_data = todo_data.model_dump(exclude_unset=True)

    if "completed" in update_data and todo_data.completed is not None:
        todo.completed = todo_data.completed

    if update_data.get("title") is not None:
        todo.title = update_data["title"]
    if "description" in update_data:
        todo.description = update_data["description"]

    updated_todo = await update_todo(db, todo, {})

    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return TodoResponse(
        id=updated_todo.id,
        title=updated_todo.title,
        description=updated_todo.description,
        completed=updated_todo.completed,
        user_id=updated_todo.user_id,
        created_at=updated_todo.created_at,
        updated_at=updated_todo.updated_at,
        user_email=current_user.email,
        tags=[TagResponse.model_validate(t) for t in updated_todo.tags],
    )


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
            detail="Not authorized to delete this todo",
        )

    await delete_todo(db, todo)

    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return None


# ── Tier 4 Endpoints: Tag Mapping & Bulk Updates ──────────────────

@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag_to_todo(
    todo_id: uuid.UUID,
    payload: dict[str, uuid.UUID],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
) -> Any:
    """Attach a tag to a todo. Requires ownership of both todo and tag."""
    tag_id = payload.get("tag_id")
    if not tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tag_id is required",
        )

    # Verify todo ownership
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this todo")

    # Verify tag ownership
    tag_res = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = tag_res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if tag.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to use this tag")

    # Attach tag if not already attached
    if tag not in todo.tags:
        todo.tags.append(tag)
        await db.commit()
        await db.refresh(todo)

    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=current_user.email,
        tags=[TagResponse.model_validate(t) for t in todo.tags],
    )


@router.delete("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
async def detach_tag_from_todo(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
) -> Any:
    """Detach a tag from a todo."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this todo")

    tag_res = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = tag_res.scalar_one_or_none()
    if tag and tag in todo.tags:
        todo.tags.remove(tag)
        await db.commit()
        await db.refresh(todo)

    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=current_user.email,
        tags=[TagResponse.model_validate(t) for t in todo.tags],
    )


@router.patch("/bulk-status", response_model=dict[str, Any])
async def bulk_update_status(
    payload: BulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
) -> Any:
    """Bulk update completed status for multiple todos in a single database transaction."""
    # Verify ownership of all todo_ids
    result = await db.execute(
        select(Todo).where(
            Todo.id.in_(payload.todo_ids),
            Todo.user_id == current_user.id,
        )
    )
    user_todos = result.scalars().all()

    if len(user_todos) != len(set(payload.todo_ids)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="One or more todo IDs do not belong to the authenticated user",
        )

    for todo in user_todos:
        todo.completed = payload.completed

    await db.commit()

    # Invalidate cache
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return {
        "message": f"Successfully updated {len(user_todos)} todos",
        "updated_count": len(user_todos),
        "completed": payload.completed,
    }
