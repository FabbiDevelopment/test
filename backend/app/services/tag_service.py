import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate


async def get_tags(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    """Get all tags of the user."""
    query = select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_tag_by_id(
    db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID
) -> Tag | None:
    """Get a specific tag by ID and user ID."""
    query = select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_tag(
    db: AsyncSession, tag_data: TagCreate, user_id: uuid.UUID
) -> Tag:
    """Create a new tag with case-insensitive uniqueness per user."""
    query = select(Tag).where(
        Tag.user_id == user_id,
        func.lower(Tag.name) == func.lower(tag_data.name.strip()),
    )
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists",
        )

    tag = Tag(
        name=tag_data.name.strip(),
        color=tag_data.color,
        user_id=user_id,
    )
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def update_tag(
    db: AsyncSession, tag: Tag, tag_data: TagUpdate
) -> Tag:
    """Update a tag with case-insensitive uniqueness check."""
    update_dict = tag_data.model_dump(exclude_unset=True)
    if "name" in update_dict and update_dict["name"]:
        new_name = update_dict["name"].strip()
        query = select(Tag).where(
            Tag.user_id == tag.user_id,
            Tag.id != tag.id,
            func.lower(Tag.name) == func.lower(new_name),
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists",
            )
        tag.name = new_name

    if "color" in update_dict:
        tag.color = update_dict["color"]

    await db.flush()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    """Delete a tag."""
    await db.delete(tag)
    await db.flush()
