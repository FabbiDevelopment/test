import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.tag import Tag, TodoTag
from app.models.todo import Todo
from app.models.user import User
from app.schemas.tag import BulkStatusUpdate
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
    """Get paginated and filtered list of todos."""
    skip = (page - 1) * size

    cache_key = f"todos:{current_user.id}:list:{page}:{size}:{status_filter}:{tag_id}:{keyword}:{date_from}:{date_to}"

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
        status_filter=status_filter,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )

    items = []
    for todo in todos:
        user_result = await db.execute(select(User).where(User.id == todo.user_id))
        user = user_result.scalar_one_or_none()
        items.append(
            TodoResponse(
                id=todo.id,
                title=todo.title,
                description=todo.description,
                completed=todo.completed,
                user_id=todo.user_id,
                created_at=todo.created_at,
                updated_at=todo.updated_at,
                user_email=user.email if user else None,
                tags=todo.tags,
            )
        )

    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )

    # Cache the response
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)

    return response


@router.patch("/bulk-status", status_code=status.HTTP_200_OK)
async def bulk_update_status(
    bulk_data: BulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Bulk update completion status of todos in a transaction."""
    # Verify all todos belong to current user
    query = select(Todo).where(
        Todo.id.in_(bulk_data.todo_ids),
        Todo.user_id == current_user.id,
    )
    result = await db.execute(query)
    user_todos = list(result.scalars().all())

    if len(user_todos) != len(set(bulk_data.todo_ids)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="One or more todos not found or do not belong to current user",
        )

    for todo in user_todos:
        todo.completed = bulk_data.completed

    await db.flush()
    await redis.delete_pattern(f"todos:{current_user.id}:list:*")
    return {"message": "Bulk status updated successfully", "updated_count": len(user_todos)}


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Create a new todo item."""
    todo = await create_todo(db, todo_data, current_user.id)
    await redis.delete_pattern(f"todos:{current_user.id}:list:*")
    return todo


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

    return todo


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
    await redis.delete_pattern(f"todos:{current_user.id}:list:*")

    return updated_todo


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
    await redis.delete_pattern(f"todos:{current_user.id}:list:*")

    return None


@router.post("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
async def attach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach a tag to a todo item."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")

    tag_res = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id))
    tag = tag_res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    existing = await db.execute(select(TodoTag).where(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id))
    if not existing.scalar_one_or_none():
        todo_tag = TodoTag(todo_id=todo_id, tag_id=tag_id)
        db.add(todo_tag)
        await db.flush()

    await redis.delete_pattern(f"todos:{current_user.id}:list:*")
    return {"message": "Tag attached successfully"}


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Detach a tag from a todo item."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")

    existing = await db.execute(select(TodoTag).where(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id))
    todo_tag = existing.scalar_one_or_none()
    if todo_tag:
        await db.delete(todo_tag)
        await db.flush()

    await redis.delete_pattern(f"todos:{current_user.id}:list:*")
    return None
