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
from app.models.tag import Tag
from app.models.todo import Todo
from app.models.todo_tag import TodoTag
from app.schemas.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate, TodoBulkUpdate, TagAttach
from app.services.todo_service import (
    create_todo,
    delete_todo,
    get_todo_by_id,
    get_todos,
    update_todo,
)

router = APIRouter()

CACHE_TTL = 300  # 5 minutes

async def invalidate_todo_cache(redis: RedisClient, user_id: uuid.UUID):
    keys = await redis.client.keys(f"todos:list:{user_id}*")
    if keys:
        await redis.client.delete(*keys)


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    status: bool | None = Query(None),
    tag_id: uuid.UUID | None = Query(None),
    keyword: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated list of todos."""
    skip = (page - 1) * size

    cache_key = f"todos:list:{current_user.id}:{status}:{tag_id}:{keyword}:{date_from}:{date_to}:{page}:{size}"

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
        status=status,
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
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

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
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_data = todo_data.model_dump()

    if todo_data.completed is not None:
        todo.completed = todo_data.completed

    # Apply other updates
    if update_data.get("title") is not None:
        todo.title = update_data["title"]
    if "description" in update_data:
        todo.description = update_data["description"]

    updated_todo = await update_todo(db, todo, {})
    
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
    todo = await get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    
    if todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    await delete_todo(db, todo)
    
    await invalidate_todo_cache(redis, current_user.id)

    return None

@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def attach_tag(
    todo_id: uuid.UUID,
    attach_data: TagAttach,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach a tag to a todo."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")
        
    tag = await db.get(Tag, attach_data.tag_id)
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    existing = await db.execute(
        select(TodoTag).where(TodoTag.todo_id == todo.id, TodoTag.tag_id == tag.id)
    )
    if not existing.scalar_one_or_none():
        todo_tag = TodoTag(todo_id=todo.id, tag_id=tag.id)
        db.add(todo_tag)
        await db.commit()
        
    await invalidate_todo_cache(redis, current_user.id)
    
    from sqlalchemy.orm import selectinload
    res = await db.execute(select(Todo).where(Todo.id == todo.id).options(selectinload(Todo.tags)))
    return res.scalar_one()

@router.delete("/{todo_id}/tags/{tag_id}", response_model=TodoResponse)
async def detach_tag(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Detach a tag from a todo."""
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")
        
    stmt = select(TodoTag).where(TodoTag.todo_id == todo.id, TodoTag.tag_id == tag_id)
    result = await db.execute(stmt)
    todo_tag = result.scalar_one_or_none()
    
    if todo_tag:
        await db.delete(todo_tag)
        await db.commit()
        
    await invalidate_todo_cache(redis, current_user.id)
    
    from sqlalchemy.orm import selectinload
    res = await db.execute(select(Todo).where(Todo.id == todo.id).options(selectinload(Todo.tags)))
    return res.scalar_one()

@router.patch("/bulk-status")
async def bulk_update_status(
    bulk_data: TodoBulkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Bulk update todo status."""
    from sqlalchemy import update
    
    stmt = (
        update(Todo)
        .where(Todo.id.in_(bulk_data.todo_ids), Todo.user_id == current_user.id)
        .values(completed=bulk_data.completed)
    )
    await db.execute(stmt)
    await db.commit()
    
    await invalidate_todo_cache(redis, current_user.id)
    return {"status": "success"}
