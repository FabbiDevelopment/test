import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
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


def todo_cache_pattern(user_id: uuid.UUID) -> str:
    return f"todos:list:{user_id}:*"


async def invalidate_todo_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    await redis.delete_pattern(todo_cache_pattern(user_id))


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated list of todos."""
    skip = (page - 1) * size
    cache_key = f"todos:list:{current_user.id}:{page}:{size}"

    cached = await redis.get(cache_key)
    if cached:
        return TodoListResponse(**json.loads(cached))

    todos, total = await get_todos(db, user_id=current_user.id, skip=skip, limit=size)
    items = [
        TodoResponse.model_validate(todo).model_copy(
            update={"user_email": current_user.email}
        )
        for todo in todos
    ]
    response = TodoListResponse(items=items, total=total, page=page, size=size)

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
    await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific todo by ID."""
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
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
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    updated_todo = await update_todo(
        db, todo, todo_data.model_dump(exclude_unset=True)
    )
    await invalidate_todo_cache(redis, current_user.id)
    return updated_todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a todo item."""
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    await delete_todo(db, todo)
    await invalidate_todo_cache(redis, current_user.id)
    return None
