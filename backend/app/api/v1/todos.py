import json
import uuid
from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.todo import Todo
from app.models.user import User
from app.schemas.tag import TagResponse
from app.schemas.todo import (
    TodoBulkStatusResponse,
    TodoBulkStatusUpdate,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoTagAttach,
    TodoUpdate,
)
from app.services.tag_service import get_tag_by_id
from app.services.todo_cache_service import (
    commit_todo_mutation,
    todo_cache_version_key,
)
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

CACHE_TTL = 300  # 5 minutes
MAX_TODO_PAGE_SIZE = 100
DEFAULT_TODO_PAGE_SIZE = 20


def todo_list_cache_key(
    user_id: uuid.UUID,
    version: str,
    page: int,
    size: int,
    status_filter: bool | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> str:
    status_value = "all" if status_filter is None else str(status_filter).lower()
    tag_value = str(tag_id) if tag_id else "all"
    keyword_value = quote(keyword or "", safe="") or "all"
    date_from_value = date_from.isoformat() if date_from else "all"
    date_to_value = date_to.isoformat() if date_to else "all"
    return (
        f"todos:list:{user_id}:v{version}:page={page}:size={size}:"
        f"status={status_value}:tag_id={tag_value}:keyword={keyword_value}:"
        f"date_from={date_from_value}:date_to={date_to_value}"
    )


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int | None = Query(None, ge=1, le=MAX_TODO_PAGE_SIZE),
    page_size: int | None = Query(None, ge=1, le=MAX_TODO_PAGE_SIZE),
    status_filter: bool | None = Query(None, alias="status"),
    tag_id: uuid.UUID | None = Query(None),
    keyword: str | None = Query(None, max_length=200),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get a filtered, owner-scoped, paginated list of Todos."""
    if size is not None and page_size is not None and size != page_size:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="size and page_size must match when both are provided",
        )
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must not be after date_to",
        )
    if tag_id and not await get_tag_by_id(db, tag_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    normalized_keyword = keyword.strip() if keyword else None
    normalized_keyword = normalized_keyword or None
    effective_size = page_size or size or DEFAULT_TODO_PAGE_SIZE
    skip = (page - 1) * effective_size

    cache_version = await redis.get(todo_cache_version_key(current_user.id)) or "0"
    cache_key = todo_list_cache_key(
        current_user.id,
        cache_version,
        page,
        effective_size,
        status_filter,
        tag_id,
        normalized_keyword,
        date_from,
        date_to,
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
        limit=effective_size,
        status=status_filter,
        tag_id=tag_id,
        keyword=normalized_keyword,
        date_from=date_from,
        date_to=date_to,
    )
    items = [todo_response(todo, todo.user.email) for todo in todos]

    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        size=effective_size,
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
    await commit_todo_mutation(db, redis, current_user.id)
    return todo_response(todo)


@router.patch("/bulk-status", response_model=TodoBulkStatusResponse)
async def bulk_update_existing_todos(
    update_data: TodoBulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update the completion state of only the caller's Todos atomically."""
    todos = await bulk_update_todo_status(
        db,
        update_data.todo_ids,
        current_user.id,
        update_data.completed,
    )
    if todos is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    await commit_todo_mutation(db, redis, current_user.id)
    return TodoBulkStatusResponse(
        updated_count=len(todos),
        completed=update_data.completed,
    )


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific todo by ID."""
    todo = await get_todo_by_id(db, todo_id, user_id=current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    return todo_response(todo)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_id: uuid.UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update a todo item."""
    todo = await get_todo_by_id(db, todo_id, user_id=current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    update_data = todo_data.model_dump(exclude_unset=True)
    updated_todo = await update_todo(db, todo, update_data)
    await commit_todo_mutation(db, redis, current_user.id)

    return todo_response(updated_todo)


@router.post("/{todo_id}/tags", status_code=status.HTTP_204_NO_CONTENT)
async def attach_tag(
    todo_id: uuid.UUID,
    tag_data: TodoTagAttach,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach one of the caller's Tags to one of the caller's Todos."""
    todo = await get_todo_by_id(db, todo_id, user_id=current_user.id)
    tag = await get_tag_by_id(db, tag_data.tag_id, current_user.id)
    if not todo or not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo or tag not found",
        )
    try:
        await attach_tag_to_todo(db, todo.id, tag.id)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag is already attached to this Todo",
        ) from None
    await commit_todo_mutation(db, redis, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Detach one of the caller's Tags from one of the caller's Todos."""
    todo = await get_todo_by_id(db, todo_id, user_id=current_user.id)
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not todo or not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo or tag not found",
        )
    if not await detach_tag_from_todo(db, todo.id, tag.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag is not attached to this Todo",
        )
    await commit_todo_mutation(db, redis, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a todo item."""
    todo = await get_todo_by_id(db, todo_id, user_id=current_user.id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    await delete_todo(db, todo)
    await commit_todo_mutation(db, redis, current_user.id)

    return None


def todo_response(todo: Todo, user_email: str | None = None) -> TodoResponse:
    """Serialize loaded Todo data without triggering async lazy relationship loads."""
    tags = todo.__dict__.get("tags", [])
    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=user_email,
        tags=[TagResponse.model_validate(tag) for tag in tags],
    )
