import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.todo import (
    BulkStatusUpdate,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.schemas.tag import AttachTagRequest
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


def _build_cache_key(user_id, page, size, status, tag_id, keyword, date_from, date_to):
    return (
        f"todos:list:{user_id}:{page}:{size}"
        f":{status}:{tag_id}:{keyword}:{date_from}:{date_to}"
    )


def _todo_to_response(todo, user_email: str | None = None) -> TodoResponse:
    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=user_email,
        tags=todo.tags,
    )


# ── List / Create ─────────────────────────────────────────────────────────────

@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(active|completed)$"),
    tag_id: uuid.UUID | None = Query(None),
    keyword: str | None = Query(None, max_length=200),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated, filtered list of todos."""
    skip = (page - 1) * size
    cache_key = _build_cache_key(
        current_user.id, page, size, status, tag_id, keyword, date_from, date_to
    )

    cached = await redis.get(cache_key)
    if cached:
        return TodoListResponse(**json.loads(cached))

    todos, total = await get_todos(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=size,
        status=status,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )

    items = [_todo_to_response(t, current_user.email) for t in todos]
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
    await db.commit()
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return _todo_to_response(todo, current_user.email)


# ── Bulk update (must be before /{todo_id} to avoid route collision) ──────────

@router.patch("/bulk-status", response_model=dict)
async def bulk_update_todo_status(
    payload: BulkStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Bulk update completed status for multiple todos in a single transaction."""
    affected = await bulk_update_status(
        db,
        todo_ids=payload.todo_ids,
        user_id=current_user.id,
        completed=payload.completed,
    )
    await db.commit()
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return {"updated": affected}


# ── Single todo ───────────────────────────────────────────────────────────────

@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific todo by ID."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this todo")
    return _todo_to_response(todo, current_user.email)


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this todo")

    update_data = todo_data.model_dump(exclude_unset=True)
    updated_todo = await update_todo(db, todo, update_data)
    await db.commit()
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return _todo_to_response(updated_todo, current_user.email)


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this todo")
    await delete_todo(db, todo)
    await db.commit()
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return None


# ── Tag attachment / detachment ───────────────────────────────────────────────

@router.post("/{todo_id}/tags", response_model=TodoResponse, status_code=status.HTTP_200_OK)
async def attach_tag(
    todo_id: uuid.UUID,
    payload: AttachTagRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach a tag to a todo. Both must belong to the authenticated user."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    tag = await get_tag_by_id(db, payload.tag_id, current_user.id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found or does not belong to you")

    todo = await attach_tag_to_todo(db, todo, tag)
    await db.commit()
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return _todo_to_response(todo, current_user.email)


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Detach a tag from a todo."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    try:
        await detach_tag_from_todo(db, todo, tag)
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return None
