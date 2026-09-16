import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.tag import Tag, TodoTag
from app.schemas.tag import TagCreate, TagUpdate

async def get_tags_by_user(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    query = select(Tag).where(Tag.user_id == user_id).order_by(Tag.name)
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_tag_by_id(db: AsyncSession, tag_id: uuid.UUID) -> Tag | None:
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    return result.scalar_one_or_none()

async def create_tag(db: AsyncSession, user_id: uuid.UUID, tag_data: TagCreate) -> Tag:
    query = select(Tag).where(Tag.user_id == user_id, func.lower(Tag.name) == tag_data.name.lower())
    existing = await db.execute(query)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    tag = Tag(name=tag_data.name, color=tag_data.color, user_id=user_id)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag

async def update_tag(db: AsyncSession, tag: Tag, update_data: TagUpdate) -> Tag:
    if update_data.name is not None and update_data.name.lower() != tag.name.lower():
        query = select(Tag).where(Tag.user_id == tag.user_id, func.lower(Tag.name) == update_data.name.lower())
        existing = await db.execute(query)
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Tag already exists")
        tag.name = update_data.name
    
    if update_data.color is not None:
        tag.color = update_data.color
        
    await db.flush()
    await db.refresh(tag)
    return tag

async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    await db.delete(tag)
    await db.flush()

async def get_todo_tag(db: AsyncSession, todo_id: uuid.UUID, tag_id: uuid.UUID) -> TodoTag | None:
    query = select(TodoTag).where(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def attach_tag_to_todo(db: AsyncSession, todo_id: uuid.UUID, tag_id: uuid.UUID) -> TodoTag:
    todo_tag = TodoTag(todo_id=todo_id, tag_id=tag_id)
    db.add(todo_tag)
    await db.flush()
    return todo_tag

async def detach_tag_from_todo(db: AsyncSession, todo_id: uuid.UUID, tag_id: uuid.UUID) -> None:
    todo_tag = await get_todo_tag(db, todo_id, tag_id)
    if todo_tag:
        await db.delete(todo_tag)
        await db.flush()
