import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate


async def get_tags(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    """Return all tags belonging to the current user, ordered by name."""
    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id).order_by(Tag.name)
    )
    return list(result.scalars().all())


async def get_tag_by_id(
    db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID
) -> Tag | None:
    """Return a tag only if it belongs to user_id."""
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_tag(
    db: AsyncSession, tag_data: TagCreate, user_id: uuid.UUID
) -> Tag:
    """Create a new tag. Raises ValueError on duplicate name (case-insensitive)."""
    tag = Tag(
        user_id=user_id,
        name=tag_data.name,
        color=tag_data.color,
    )
    db.add(tag)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise ValueError(f"Tag '{tag_data.name}' already exists for this user.")
    await db.refresh(tag)
    return tag


async def update_tag(
    db: AsyncSession, tag: Tag, tag_data: TagUpdate
) -> Tag:
    """Partially update a tag. Raises ValueError on duplicate name."""
    update_fields = tag_data.model_dump(exclude_unset=True)
    for key, value in update_fields.items():
        setattr(tag, key, value)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise ValueError(f"Tag name already exists for this user.")
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    """Delete a tag (cascade removes todo_tags rows automatically)."""
    await db.delete(tag)
    await db.flush()
