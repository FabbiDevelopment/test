import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.tag_service import create_tag, get_tag, list_tags, tag_name_exists
from app.api.v1.todos import invalidate_todo_cache

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def get_tags(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await list_tags(db, current_user.id)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def add_tag(data: TagCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if await tag_name_exists(db, current_user.id, data.name):
        raise HTTPException(status_code=409, detail="Tag name already exists")
    return await create_tag(db, data, current_user.id)


@router.patch("/{tag_id}", response_model=TagResponse)
async def edit_tag(tag_id: uuid.UUID, data: TagUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    tag = await get_tag(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    values = data.model_dump(exclude_unset=True)
    if "name" in values and await tag_name_exists(db, current_user.id, values["name"], tag.id):
        raise HTTPException(status_code=409, detail="Tag name already exists")
    for key, value in values.items():
        setattr(tag, key, value)
    await db.flush()
    await db.refresh(tag)
    await invalidate_todo_cache(redis, current_user.id)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag(tag_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    tag = await get_tag(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    await db.delete(tag)
    await db.flush()
    await invalidate_todo_cache(redis, current_user.id)