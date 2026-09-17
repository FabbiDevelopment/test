import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.todo import (
    BulkTodoStatusResponse,
    BulkTodoStatusUpdate,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoStatus,
    TodoTagCreate,
    TodoUpdate,
)
from app.services.cache_service import build_todo_cache_key, invalidate_todo_cache
from app.services.tag_service import get_tag_by_id
from app.services.todo_service import (
    bulk_update_todo_status,
    create_todo,
    delete_todo,
    get_todo_by_id,
    get_todos,
    update_todo,
)

router = APIRouter()

CACHE_TTL = 300


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    size: int | None = Query(default=None, ge=1, le=100, include_in_schema=False),
    status_filter: TodoStatus | None = Query(default=None, alias="status"),
    tag_id: uuid.UUID | None = Query(default=None),
    keyword: str | None = Query(default=None, max_length=200),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get the current user's filtered and paginated todos."""
    effective_page_size = size or page_size
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be before or equal to date_to",
        )

    cache_key = build_todo_cache_key(
        current_user.id,
        page=page,
        page_size=effective_page_size,
        status=status_filter,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )
    cached = await redis.get(cache_key)
    if cached:
        return TodoListResponse(**json.loads(cached))

    skip = (page - 1) * effective_page_size
    todos, total = await get_todos(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=effective_page_size,
        status=status_filter,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )
    response = TodoListResponse(
        items=[
            TodoResponse.model_validate(todo).model_copy(
                update={"user_email": current_user.email}
            )
            for todo in todos
        ],
        total=total,
        page=page,
        size=effective_page_size,
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
    todo = await create_todo(db, todo_data, current_user.id)
    await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.patch("/bulk-status", response_model=BulkTodoStatusResponse)
async def update_bulk_status(
    update_data: BulkTodoStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Atomically update status only when every Todo belongs to the user."""
    updated_todos = await bulk_update_todo_status(
        db,
        todo_ids=update_data.todo_ids,
        completed=update_data.completed,
        user_id=current_user.id,
    )
    if updated_todos is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more todos were not found",
        )

    await invalidate_todo_cache(redis, current_user.id)
    return BulkTodoStatusResponse(
        updated_count=len(updated_todos),
        items=[TodoResponse.model_validate(todo) for todo in updated_todos],
    )


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    updated_todo = await update_todo(
        db,
        todo,
        todo_data.model_dump(exclude_unset=True),
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
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    await delete_todo(db, todo)
    await invalidate_todo_cache(redis, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag_to_todo(
    todo_id: uuid.UUID,
    tag_data: TodoTagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    tag = await get_tag_by_id(db, tag_data.tag_id, current_user.id)
    if todo is None or tag is None:
        raise HTTPException(status_code=404, detail="Todo or tag not found")

    if all(existing.id != tag.id for existing in todo.tags):
        todo.tags.append(tag)
        await db.flush()
        await db.refresh(todo, attribute_names=["tags"])

    await invalidate_todo_cache(redis, current_user.id)
    return todo


@router.delete(
    "/{todo_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def detach_tag_from_todo(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    attached_tag = next((tag for tag in todo.tags if tag.id == tag_id), None)
    if attached_tag is None:
        raise HTTPException(status_code=404, detail="Tag is not attached to todo")

    todo.tags.remove(attached_tag)
    await db.flush()
    await invalidate_todo_cache(redis, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
