import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.models.todo import Todo
from app.schemas.tag import TagCreate, TagUpdate


async def get_tags(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    """List all tags belonging to the user."""
    stmt = (
        select(Tag)
        .where(Tag.user_id == user_id)
        .order_by(func.lower(Tag.name).asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_tag_by_id(
    db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID | None = None
) -> Tag | None:
    """Get a tag by ID, optionally verifying user ownership."""
    stmt = select(Tag).where(Tag.id == tag_id)
    if user_id is not None:
        stmt = stmt.where(Tag.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_tag(
    db: AsyncSession, user_id: uuid.UUID, tag_data: TagCreate
) -> Tag:
    """Create a new tag for the user with case-insensitive uniqueness check."""
    cleaned_name = tag_data.name.strip()
    # Check duplicate case-insensitively
    existing = await db.execute(
        select(Tag).where(
            Tag.user_id == user_id,
            func.lower(Tag.name) == cleaned_name.lower(),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag with name '{cleaned_name}' already exists",
        )

    tag = Tag(
        user_id=user_id,
        name=cleaned_name,
        color=tag_data.color or "#3B82F6",
    )
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def update_tag(
    db: AsyncSession, tag: Tag, tag_data: TagUpdate
) -> Tag:
    """Update a tag with case-insensitive uniqueness check."""
    if tag_data.name is not None:
        cleaned_name = tag_data.name.strip()
        existing = await db.execute(
            select(Tag).where(
                Tag.user_id == tag.user_id,
                Tag.id != tag.id,
                func.lower(Tag.name) == cleaned_name.lower(),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag with name '{cleaned_name}' already exists",
            )
        tag.name = cleaned_name

    if tag_data.color is not None:
        tag.color = tag_data.color

    await db.flush()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    """Delete a tag and its associations."""
    await db.delete(tag)
    await db.flush()


async def attach_tag_to_todo(
    db: AsyncSession, todo: Todo, tag: Tag
) -> None:
    """Attach a tag to a todo if not already attached."""
    if tag.user_id != todo.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot attach a tag belonging to another user",
        )

    if tag not in todo.tags:
        todo.tags.append(tag)
        await db.flush()
        await db.refresh(todo)


async def detach_tag_from_todo(
    db: AsyncSession, todo: Todo, tag: Tag
) -> None:
    """Detach a tag from a todo."""
    if tag.user_id != todo.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot detach a tag belonging to another user",
        )

    if tag in todo.tags:
        todo.tags.remove(tag)
        await db.flush()
        await db.refresh(todo)
