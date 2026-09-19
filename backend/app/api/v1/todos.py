from datetime import datetime
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.todo import (
    TodoBulkStatusUpdate,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.services.tag_service import get_tag_by_id
from app.services.todo_service import (
    attach_tag_to_todo,
    bulk_update_todo_status,
    create_todo,
    delete_todo,
    detach_tag_from_todo,
    get_todo_by_id,
    get_todos,
    update_todo,
)

router = APIRouter()

CACHE_TTL = 300  # 5 phút (300 giậy)


class AttachTagPayload(BaseModel):
    tag_id: uuid.UUID


async def invalidate_user_todos_cache(redis: RedisClient, user_id: uuid.UUID) -> None:

    try:
        if redis.client:
            keys = await redis.client.keys(f"todos:list:{user_id}:*")
            if keys:
                await redis.client.delete(*keys)
    except Exception:
        pass


@router.get("", response_model=TodoListResponse)
async def list_todos(
    status_filter: str | None = Query(None, alias="status", description="Lọc theo trạng thái: all / completed / pending"),
    tag_id: uuid.UUID | None = Query(None, description="Lọc theo Tag ID"),
    keyword: str | None = Query(None, description="Từ khóa tìm kiếm trong title hoặc description"),
    date_from: datetime | None = Query(None, description="Thời gian bắt đầu (từ ngày)"),
    date_to: datetime | None = Query(None, description="Thời gian kết thúc (đến ngày)"),
    page: int = Query(1, ge=1, description="Trang hiện tại (bắt đầu từ 1)"),
    size: int = Query(20, ge=1, description="Số lượng bản ghi mỗi trang"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    skip = (page - 1) * size

    cache_key = (
        f"todos:list:{current_user.id}:st:{status_filter}:tag:{tag_id}:"
        f"kw:{keyword}:df:{date_from}:dt:{date_to}:p:{page}:s:{size}"
    )

   
    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return TodoListResponse(**cached_data)

    
    todos, total = await get_todos(
        db,
        user_id=current_user.id,
        status=status_filter,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=size,
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
            tags=todo.tags,
        )
        for todo in todos
    ]
    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )

    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)

    return response


@router.patch("/bulk-status", status_code=status.HTTP_200_OK)
async def bulk_update_status(
    payload: TodoBulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
   
    async with db.begin_nested():
        updated_count = await bulk_update_todo_status(
            db,
            user_id=current_user.id,
            todo_ids=payload.todo_ids,
            completed=payload.completed,
        )


    if updated_count != len(payload.todo_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="One or more todo items do not belong to the current user",
        )

    await db.commit()
    await invalidate_user_todos_cache(redis, current_user.id)

    return {
        "message": f"Successfully updated {updated_count} todo items",
        "updated_count": updated_count,
    }


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    
    todo = await create_todo(db, todo_data, current_user.id)
    await invalidate_user_todos_cache(redis, current_user.id)
    return todo


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    
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

    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    
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

    if update_data.get("title") is not None:
        todo.title = update_data["title"]
    if "description" in update_data:
        todo.description = update_data["description"]

    updated_todo = await update_todo(db, todo, {})
    await invalidate_user_todos_cache(redis, current_user.id)

    return updated_todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    
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
    await invalidate_user_todos_cache(redis, current_user.id)

    return None


@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag_to_todo_endpoint(
    todo_id: uuid.UUID,
    payload: AttachTagPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
   
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
            detail="Not authorized to use this tag",
        )

    updated_todo = await attach_tag_to_todo(db, todo=todo, tag=tag)
    await invalidate_user_todos_cache(redis, current_user.id)
    return updated_todo


@router.delete("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
async def detach_tag_from_todo_endpoint(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
   
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

    updated_todo = await detach_tag_from_todo(db, todo=todo, tag=tag)
    await invalidate_user_todos_cache(redis, current_user.id)
    return updated_todo
