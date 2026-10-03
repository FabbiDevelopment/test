import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select, exc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def read_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve tags for current user."""
    stmt = select(Tag).where(Tag.user_id == current_user.id).order_by(Tag.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    *,
    db: AsyncSession = Depends(get_db),
    tag_in: TagCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create new tag."""
    tag = Tag(**tag_in.model_dump(), user_id=current_user.id)
    db.add(tag)
    try:
        await db.commit()
        await db.refresh(tag)
    except exc.IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Tag with this name already exists",
        )
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    *,
    db: AsyncSession = Depends(get_db),
    tag_id: uuid.UUID,
    tag_in: TagUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update a tag."""
    stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    update_data = tag_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)
        
    try:
        await db.commit()
        await db.refresh(tag)
    except exc.IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Tag with this name already exists",
        )
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_tag(
    *,
    db: AsyncSession = Depends(get_db),
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a tag."""
    stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    await db.delete(tag)
    await db.commit()
    return None
