import hashlib
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.todo import Todo
from app.models.user import User
from app.schemas.tag import TagResponse
from app.schemas.todo import (
    BulkTodoStatusUpdate,
    TodoCreate,
    TodoListParams,
    TodoListResponse,
    TodoResponse,
    TodoTagCreate,
    TodoUpdate,
)
from app.services.tag_service import get_user_tag
from app.services.todo_service import (
    attach_tag,
    bulk_update_todo_status,
    create_todo,
    detach_tag,
    delete_todo,
    get_todo_by_id,
    get_todos,
    update_todo,
)

router = APIRouter()

CACHE_TTL = 300  # 5 minutes


def todo_list_cache_key(
    user_id: uuid.UUID,
    params: TodoListParams,
) -> str:
    query = {
        "page": params.page,
        "page_size": params.effective_page_size,
        "status": params.status or "all",
        "tag_id": str(params.tag_id) if params.tag_id else None,
        "keyword": (
            params.normalized_keyword.casefold() if params.normalized_keyword else None
        ),
        "date_from": params.date_from.isoformat() if params.date_from else None,
        "date_to": params.date_to.isoformat() if params.date_to else None,
    }
    digest = hashlib.sha256(
        json.dumps(query, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return f"todos:{user_id}:list:{digest}"


async def invalidate_user_todos(redis: RedisClient, user_id: uuid.UUID) -> None:
    await redis.delete_pattern(f"todos:{user_id}:list:*")


def serialize_todo(todo: Todo) -> TodoResponse:
    response = TodoResponse.model_validate(todo)
    response.user_email = todo.user.email if todo.user else None
    return response


@router.get("", response_model=TodoListResponse)
async def list_todos(
    params: Annotated[TodoListParams, Query()],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """List the caller's todos with optional filters and user-scoped caching."""
    if params.tag_id and await get_user_tag(db, params.tag_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    cache_key = todo_list_cache_key(current_user.id, params)
    cached = await redis.get(cache_key)
    if cached:
        return TodoListResponse(**json.loads(cached))

    todos, total = await get_todos(db, current_user.id, params)
    response = TodoListResponse(
        items=[serialize_todo(todo) for todo in todos],
        total=total,
        page=params.page,
        size=params.effective_page_size,
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
    """Create a new todo item."""
    todo = await create_todo(db, todo_data, current_user.id)
    todo_id = todo.id
    await db.commit()
    await invalidate_user_todos(redis, current_user.id)
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    return serialize_todo(todo)


@router.patch(
    "/bulk-status",
    status_code=status.HTTP_200_OK,
)
async def update_todos_status(
    update_data: BulkTodoStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Atomically update completion for todos owned by the caller."""
    updated_count = await bulk_update_todo_status(
        db,
        current_user.id,
        update_data.todo_ids,
        update_data.completed,
    )
    if updated_count is None:
        raise HTTPException(status_code=404, detail="One or more todos not found")

    await db.commit()
    await invalidate_user_todos(redis, current_user.id)
    return {"updated": updated_count}


@router.post(
    "/{todo_id}/tags",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_tag_to_todo(
    todo_id: uuid.UUID,
    tag_data: TodoTagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach one of the caller's tags to one of the caller's todos."""
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    tag = await get_user_tag(db, tag_data.tag_id, current_user.id)
    if todo is None or tag is None:
        raise HTTPException(status_code=404, detail="Todo or tag not found")
    if not attach_tag(todo, tag):
        raise HTTPException(status_code=409, detail="Tag is already attached")

    await db.commit()
    await invalidate_user_todos(redis, current_user.id)
    return TagResponse.model_validate(tag)


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag_from_todo(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Detach one of the caller's tags from one of the caller's todos."""
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    tag = await get_user_tag(db, tag_id, current_user.id)
    if todo is None or tag is None:
        raise HTTPException(status_code=404, detail="Todo or tag not found")
    if not detach_tag(todo, tag):
        raise HTTPException(status_code=404, detail="Tag is not attached to todo")

    await db.commit()
    await invalidate_user_todos(redis, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific todo by ID."""
    todo = await get_todo_by_id(db, todo_id, user_id=current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return serialize_todo(todo)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update an owned todo item."""
    todo = await get_todo_by_id(db, todo_id, user_id=current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    update_data = todo_data.model_dump(exclude_unset=True)
    await update_todo(db, todo, update_data)
    await db.commit()
    await invalidate_user_todos(redis, current_user.id)
    todo = await get_todo_by_id(db, todo_id, current_user.id)
    return serialize_todo(todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete an owned todo item."""
    todo = await get_todo_by_id(db, todo_id, user_id=current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    await delete_todo(db, todo)
    await db.commit()
    await invalidate_user_todos(redis, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
