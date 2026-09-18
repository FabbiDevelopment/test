import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate
from app.services.todo_service import create_todo, delete_todo, get_todo_by_id, get_todos, todo_response, update_todo

router = APIRouter()
CACHE_TTL = 300


def cache_key(user_id: uuid.UUID, page: int, page_size: int, **filters) -> str:
    query = ":".join(f"{key}={value}" for key, value in sorted(filters.items()) if value is not None)
    return f"todos:list:{user_id}:{page}:{page_size}:{query}"


async def invalidate_user_cache(redis: RedisClient, user_id: uuid.UUID):
    for key in await redis.keys(f"todos:list:{user_id}:*"):
        await redis.delete(key)


async def owned_todo(db: AsyncSession, todo_id: uuid.UUID, user_id: uuid.UUID):
    todo = await get_todo_by_id(db, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this todo")
    return todo


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: bool | None = Query(None, alias="status"),
    tag_id: uuid.UUID | None = None,
    keyword: str | None = Query(None, max_length=100),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be before date_to")
    key = cache_key(current_user.id, page, page_size, status=status_filter, tag_id=tag_id, keyword=keyword, date_from=date_from, date_to=date_to)
    cached = await redis.get(key)
    if cached:
        return TodoListResponse.model_validate_json(cached)
    todos, total = await get_todos(
        db, current_user.id, skip=(page - 1) * page_size, limit=page_size,
        completed=status_filter, tag_id=tag_id, keyword=keyword, date_from=date_from, date_to=date_to,
    )
    response = TodoListResponse(
        items=[todo_response(todo, current_user.email) for todo in todos],
        total=total, page=page, page_size=page_size,
    )
    await redis.set(key, response.model_dump_json(), ex=CACHE_TTL)
    return response


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(todo_data: TodoCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await create_todo(db, todo_data, current_user.id)
    response = todo_response(todo, current_user.email)
    await db.commit()
    await invalidate_user_cache(redis, current_user.id)
    return response


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return todo_response(await owned_todo(db, todo_id, current_user.id), current_user.email)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(todo_id: uuid.UUID, todo_data: TodoUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await owned_todo(db, todo_id, current_user.id)
    await update_todo(db, todo, todo_data.model_dump(exclude_unset=True))
    response = todo_response(todo, current_user.email)
    await db.commit()
    await invalidate_user_cache(redis, current_user.id)
    return response


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(todo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    await delete_todo(db, await owned_todo(db, todo_id, current_user.id))
    await db.commit()
    await invalidate_user_cache(redis, current_user.id)
