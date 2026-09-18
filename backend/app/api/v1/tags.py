import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.api.v1.todos import invalidate_user_cache, owned_todo
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import AttachTagRequest, BulkStatusRequest, TagCreate, TagResponse, TagUpdate
from app.schemas.todo import TodoResponse
from app.services.tag_service import attach_tag_to_todo, bulk_update_status, create_tag, delete_tag, detach_tag_from_todo, get_tags_for_todo, get_tags_for_user, owned_tag, update_tag
from app.services.todo_service import todo_response

router = APIRouter()
todo_router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_tags_for_user(db, current_user.id)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tag(data: TagCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tag = await create_tag(db, data, current_user.id)
    await db.commit()
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_existing_tag(tag_id: uuid.UUID, data: TagUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    tag = await update_tag(db, await owned_tag(db, tag_id, current_user.id), data)
    await db.commit()
    await invalidate_user_cache(redis, current_user.id)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_tag(tag_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    await delete_tag(db, await owned_tag(db, tag_id, current_user.id))
    await db.commit()
    await invalidate_user_cache(redis, current_user.id)


@todo_router.post("/{todo_id}/tags", response_model=list[TagResponse], status_code=status.HTTP_201_CREATED)
async def attach_tag(todo_id: uuid.UUID, body: AttachTagRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todo = await owned_todo(db, todo_id, current_user.id)
    tag = await owned_tag(db, body.tag_id, current_user.id)
    await attach_tag_to_todo(db, todo.id, tag.id)
    await db.commit()
    await invalidate_user_cache(redis, current_user.id)
    return await get_tags_for_todo(db, todo.id)


@todo_router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag(todo_id: uuid.UUID, tag_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    await owned_todo(db, todo_id, current_user.id)
    await owned_tag(db, tag_id, current_user.id)
    await detach_tag_from_todo(db, todo_id, tag_id)
    await db.commit()
    await invalidate_user_cache(redis, current_user.id)


@todo_router.patch("/bulk-status", response_model=list[TodoResponse])
async def bulk_update_todo_status(body: BulkStatusRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    todos = await bulk_update_status(db, body.todo_ids, body.completed, current_user.id)
    await db.commit()
    await invalidate_user_cache(redis, current_user.id)
    return [todo_response(todo, current_user.email) for todo in todos]
