import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import Tag, TodoTag
from app.models.todo import Todo
from app.schemas.tag import TagCreate, TagUpdate


async def get_tags(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    """Get all tags for a specific user ordered by name."""
    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id).order_by(func.lower(Tag.name).asc())
    )
    return list(result.scalars().all())


async def get_tag_by_id(
    db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID
) -> Tag | None:
    """Get a specific tag by ID ensuring user ownership."""
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_tag(
    db: AsyncSession, user_id: uuid.UUID, tag_data: TagCreate
) -> Tag:
    """Create a new tag for the user, preventing case-insensitive duplicates."""
    clean_name = tag_data.name.strip()
    existing = await db.execute(
        select(Tag).where(
            Tag.user_id == user_id,
            func.lower(Tag.name) == func.lower(clean_name),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag '{clean_name}' already exists",
        )

    tag = Tag(
        user_id=user_id,
        name=clean_name,
        color=tag_data.color or "#6366f1",
    )
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def update_tag(
    db: AsyncSession, tag: Tag, tag_data: TagUpdate
) -> Tag:
    """Update tag name or color with duplicate check."""
    if tag_data.name is not None:
        clean_name = tag_data.name.strip()
        existing = await db.execute(
            select(Tag).where(
                Tag.user_id == tag.user_id,
                Tag.id != tag.id,
                func.lower(Tag.name) == func.lower(clean_name),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{clean_name}' already exists",
            )
        tag.name = clean_name

    if tag_data.color is not None:
        tag.color = tag_data.color

    await db.flush()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    """Delete a tag (cascades to todo_tags)."""
    await db.delete(tag)
    await db.flush()


async def attach_tag_to_todo(
    db: AsyncSession, todo: Todo, tag: Tag
) -> Todo:
    """Attach a tag to a todo item."""
    if not any(t.id == tag.id for t in todo.tags):
        todo.tags.append(tag)
        await db.flush()
    return todo


async def detach_tag_from_todo(
    db: AsyncSession, todo: Todo, tag_id: uuid.UUID
) -> Todo:
    """Detach a tag from a todo item."""
    todo.tags = [t for t in todo.tags if t.id != tag_id]
    await db.flush()
    return todo


async def bulk_update_status(
    db: AsyncSession,
    user_id: uuid.UUID,
    todo_ids: list[uuid.UUID],
    completed: bool,
) -> int:
    """Bulk update completed status for multiple todos owned by user in a transaction."""
    if not todo_ids:
        return 0

    # IDOR / ownership verification: Verify all todo_ids belong to user_id
    result = await db.execute(
        select(Todo.id).where(
            Todo.id.in_(todo_ids),
            Todo.user_id == user_id,
        )
    )
    owned_ids = set(result.scalars().all())

    # If any requested ID is not owned by the user, abort transaction
    if len(owned_ids) != len(set(todo_ids)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="One or more todos do not belong to current user",
        )

    # Perform bulk update
    await db.execute(
        update(Todo)
        .where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
        .values(completed=completed)
    )
    await db.flush()
    return len(todo_ids)
