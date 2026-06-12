import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.models.todo import Todo
from app.models.tag import Tag, TodoTag
from app.schemas.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate, TodoBulkUpdate
from app.schemas.tag import TagResponse
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
    status: str | None = Query(None),
    tag_id: uuid.UUID | None = Query(None),
    keyword: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated list of todos with filters."""
    skip = (page - 1) * size

    # Build a composite cache key that includes all filter parameters
    filters_key = f"status={status}&tag={tag_id}&kw={keyword}&df={date_from}&dt={date_to}"
    cache_key = f"todos:list:{current_user.id}:{page}:{size}:{filters_key}"

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
        items.append(
            TodoResponse(
                id=todo.id,
                title=todo.title,
                description=todo.description,
                completed=todo.completed,
                user_id=todo.user_id,
                created_at=todo.created_at,
                updated_at=todo.updated_at,
                user_email=current_user.email,
                tags=[TagResponse.model_validate(t) for t in todo.tags],
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
    
    keys = await redis.client.keys(f"todos:list:{current_user.id}:*")
    if keys:
        await redis.client.delete(*keys)
        
    return TodoResponse.model_validate(todo)


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

    return TodoResponse.model_validate(todo)


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

    update_data = todo_data.model_dump()

    if todo_data.completed is not None:
        todo.completed = todo_data.completed

    # Apply other updates
    if update_data.get("title") is not None:
        todo.title = update_data["title"]
    if "description" in update_data:
        todo.description = update_data["description"]

    updated_todo = await update_todo(db, todo, {})
    
    keys = await redis.client.keys(f"todos:list:{current_user.id}:*")
    if keys:
        await redis.client.delete(*keys)

    return TodoResponse.model_validate(updated_todo)


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

    keys = await redis.client.keys(f"todos:list:{current_user.id}:*")
    if keys:
        await redis.client.delete(*keys)

    return None


@router.patch("/bulk-status", status_code=status.HTTP_200_OK)
async def bulk_update_status(
    bulk_data: TodoBulkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Bulk update the status of multiple todos."""
    if not bulk_data.todo_ids:
        return {"updated_count": 0}

    # Fetch all requested todos
    query = select(Todo).where(Todo.id.in_(bulk_data.todo_ids))
    result = await db.execute(query)
    todos = result.scalars().all()

    # Verify ownership
    for t in todos:
        if t.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own todos",
            )

    for t in todos:
        t.completed = bulk_data.completed

    await db.commit()

    # Invalidate cache
    keys = await redis.client.keys(f"todos:list:{current_user.id}:*")
    if keys:
        await redis.client.delete(*keys)

    return {"updated_count": len(todos)}


@router.post("/{todo_id}/tags", status_code=status.HTTP_201_CREATED)
async def add_tag_to_todo(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID = Query(..., description="The ID of the tag to add"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Attach a tag to a todo."""
    # Verify todo ownership
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # Verify tag ownership
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalars().first()
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    # Check if already attached
    result = await db.execute(
        select(TodoTag).where(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id)
    )
    if result.scalars().first():
        return {"message": "Tag already attached"}

    # Attach
    todo_tag = TodoTag(todo_id=todo_id, tag_id=tag_id)
    db.add(todo_tag)
    await db.commit()

    # Invalidate cache
    keys = await redis.client.keys(f"todos:list:{current_user.id}:*")
    if keys:
        await redis.client.delete(*keys)

    return {"message": "Tag attached successfully"}


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_todo(
    todo_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Detach a tag from a todo."""
    # Verify todo ownership
    todo = await get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # Detach
    await db.execute(
        delete(TodoTag).where(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id)
    )
    await db.commit()

    # Invalidate cache
    keys = await redis.client.keys(f"todos:list:{current_user.id}:*")
    if keys:
        await redis.client.delete(*keys)

    return None
