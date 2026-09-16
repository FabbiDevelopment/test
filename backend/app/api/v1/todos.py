import hashlib
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import AttachTagRequest, BulkStatusRequest
from app.schemas.todo import (
    TagBrief,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.services.tag_service import (
    attach_tag_to_todo,
    detach_tag_from_todo,
    get_tag_by_id,
    get_tags_for_todo,
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


# THÊM: helper invalidate cache theo user — gọi sau mọi mutation (create/update/delete/tag/bulk)
async def _invalidate_user_todo_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    await redis.delete_by_prefix(f"todos:list:{user_id}:")


def _build_cache_key(user_id: uuid.UUID, page: int, size: int, filters: dict) -> str:
    # SAI: cache_key = "todos:list" — key toàn cục, User B nhận cache của User A (rò rỉ dữ liệu)
    # Không xóa comment SAI; dùng key scoped + filter hash bên dưới
    # cache_key = "todos:list"
    filter_hash = hashlib.md5(
        json.dumps(filters, sort_keys=True, default=str).encode()
    ).hexdigest()[:8]
    # THÊM: scope theo user + pagination + filters — Level 4
    return f"todos:list:{user_id}:{page}:{size}:{filter_hash}"


async def _todo_to_response(
    db: AsyncSession, todo, user_email: str | None = None
) -> TodoResponse:
    tags = await get_tags_for_todo(db, todo.id)
    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=user_email,
        tags=[TagBrief.model_validate(t) for t in tags],
    )


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="size"),
    status_filter: str | None = Query(None, alias="status"),
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """GET /todos — list with filtering & pagination."""
    size = page_size
    skip = (page - 1) * size

    completed: bool | None = None
    if status_filter == "completed":
        completed = True
    elif status_filter == "active":
        completed = False

    filters = {
        "status": status_filter,
        "tag_id": str(tag_id) if tag_id else None,
        "keyword": keyword,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }
    cache_key = _build_cache_key(current_user.id, page, size, filters)

    cached = await redis.get(cache_key)
    if cached:
        return TodoListResponse(**json.loads(cached))

    todos, total = await get_todos(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=size,
        completed=completed,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )

    items = []
    for todo in todos:
        user_result = await db.execute(select(User).where(User.id == todo.user_id))
        user = user_result.scalar_one_or_none()
        items.append(await _todo_to_response(db, todo, user.email if user else None))

    response = TodoListResponse(items=items, total=total, page=page, size=size)
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)
    return response


@router.patch("/bulk-status")
async def bulk_status_update(
    payload: BulkStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """PATCH /todos/bulk-status — bulk update trong single transaction (Level 4)."""
    updated_count = await bulk_update_status(
        db, current_user.id, payload.todo_ids, payload.completed
    )
    if updated_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No todos found or not authorized",
        )
    await _invalidate_user_todo_cache(redis, current_user.id)
    return {"updated": updated_count}


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),  # THÊM: inject redis để invalidate cache sau create
):
    todo = await create_todo(db, todo_data, current_user.id)
    # SAI: không invalidate cache sau create — danh sách cached thiếu todo mới tới hết TTL
    # THÊM: xóa cache user ngay sau khi tạo
    await _invalidate_user_todo_cache(redis, current_user.id)
    return await _todo_to_response(db, todo, current_user.email)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # SAI: thiếu ownership check — IDOR, user A đọc todo user B
    # THÊM: chỉ owner được truy cập
    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this todo",
        )

    return await _todo_to_response(db, todo)


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # SAI: thiếu ownership — user A sửa todo user B (IDOR)
    # THÊM: chỉ owner được cập nhật
    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this todo",
        )

    # SAI: model_dump() + if todo_data.completed: — không set False, xóa description khi PUT title
    # update_data = todo_data.model_dump()
    # if todo_data.completed:
    #     todo.completed = todo_data.completed
    # updated_todo = await update_todo(db, todo, {})
    # THÊM: exclude_unset — partial update an toàn
    update_data = todo_data.model_dump(exclude_unset=True)
    updated_todo = await update_todo(db, todo, update_data)

    # SAI: redis inject nhưng không dùng — stale cache sau update
    # THÊM: invalidate sau update
    await _invalidate_user_todo_cache(redis, current_user.id)
    return await _todo_to_response(db, updated_todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # SAI: thiếu ownership — user A xóa todo user B
    # THÊM: chỉ owner được xóa
    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this todo",
        )

    await delete_todo(db, todo)
    # SAI: không invalidate — todo đã xóa vẫn trong cache
    # THÊM: invalidate sau delete
    await _invalidate_user_todo_cache(redis, current_user.id)
    return None


@router.post("/{todo_id}/tags", status_code=status.HTTP_201_CREATED)
async def attach_tag(
    todo_id: uuid.UUID,
    payload: AttachTagRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    tag = await get_tag_by_id(db, payload.tag_id)
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tag not found or not yours")

    await attach_tag_to_todo(db, todo, tag)
    await _invalidate_user_todo_cache(redis, current_user.id)
    return {"message": "Tag attached"}


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    tag = await get_tag_by_id(db, tag_id)
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tag not found or not yours")

    await detach_tag_from_todo(db, todo_id, tag_id)
    await _invalidate_user_todo_cache(redis, current_user.id)
    return None
