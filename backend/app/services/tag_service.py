import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, TodoTag
from app.models.todo import Todo
from app.schemas.tag import TagCreate, TagSimpleResponse


async def get_tags(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    """Get all tags owned by a user, sorted alphabetically by name."""
    query = (
        select(Tag)
        .where(Tag.user_id == user_id)
        .order_by(func.lower(Tag.name).asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_tag_by_id_and_user(
    db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID
) -> Tag | None:
    """Get a specific tag by ID ensuring user ownership."""
    query = select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_tag_by_lower_name_and_user(
    db: AsyncSession, name: str, user_id: uuid.UUID
) -> Tag | None:
    """Check for existing tag with same name case-insensitively for a user."""
    query = select(Tag).where(
        Tag.user_id == user_id,
        func.lower(Tag.name) == func.lower(name.strip()),
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_tag(
    db: AsyncSession, tag_data: TagCreate, user_id: uuid.UUID
) -> Tag:
    """Create a new tag with case-insensitive uniqueness check."""
    name = tag_data.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tag name cannot be empty or whitespace",
        )

    existing = await get_tag_by_lower_name_and_user(db, name, user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag '{name}' already exists",
        )

    tag = Tag(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        color=tag_data.color or "#3b82f6",
    )
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def update_tag(
    db: AsyncSession, tag: Tag, update_data: dict
) -> Tag:
    """Update a tag's name or color with uniqueness validation."""
    if "name" in update_data and update_data["name"] is not None:
        new_name = update_data["name"].strip()
        if not new_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tag name cannot be empty or whitespace",
            )
        if new_name.lower() != tag.name.lower():
            existing = await get_tag_by_lower_name_and_user(db, new_name, tag.user_id)
            if existing and existing.id != tag.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tag '{new_name}' already exists",
                )
        update_data["name"] = new_name

    for key, value in update_data.items():
        if value is not None:
            setattr(tag, key, value)

    await db.flush()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    """Delete a tag and cascade-delete its associations."""
    await db.delete(tag)
    await db.flush()


async def attach_tag_to_todo(
    db: AsyncSession, todo: Todo, tag: Tag
) -> None:
    """Attach a tag to a todo item."""
    # Check if already attached
    query = select(TodoTag).where(
        TodoTag.todo_id == todo.id,
        TodoTag.tag_id == tag.id,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag is already attached to this todo",
        )

    todo_tag = TodoTag(todo_id=todo.id, tag_id=tag.id)
    db.add(todo_tag)
    await db.flush()



async def detach_tag_from_todo(
    db: AsyncSession, todo: Todo, tag: Tag
) -> None:
    """Detach a tag from a todo item."""
    query = select(TodoTag).where(
        TodoTag.todo_id == todo.id,
        TodoTag.tag_id == tag.id,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.flush()


async def get_tags_for_todo(db: AsyncSession, todo_id: uuid.UUID) -> list[TagSimpleResponse]:
    """Fetch only required tag fields (id, name, color) for a specific todo via column projection."""
    stmt = (
        select(Tag.id, Tag.name, Tag.color)
        .join(TodoTag, TodoTag.tag_id == Tag.id)
        .where(TodoTag.todo_id == todo_id)
        .order_by(Tag.name.asc())
    )
    result = await db.execute(stmt)
    return [TagSimpleResponse(id=row.id, name=row.name, color=row.color) for row in result.all()]

