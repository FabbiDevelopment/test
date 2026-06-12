import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, func

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.tag import Tag, TodoTag
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tags for the current user."""
    query = select(Tag).where(Tag.user_id == current_user.id).order_by(Tag.created_at.desc())
    result = await db.execute(query)
    tags = result.scalars().all()
    return tags


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tag."""
    # Check case-insensitive uniqueness
    query = select(Tag).where(
        Tag.user_id == current_user.id,
        func.lower(Tag.name) == tag_data.name.lower()
    )
    result = await db.execute(query)
    existing_tag = result.scalars().first()
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists",
        )

    tag = Tag(
        user_id=current_user.id,
        name=tag_data.name,
        color=tag_data.color,
    )
    db.add(tag)
    try:
        await db.commit()
        await db.refresh(tag)
    except exc.IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists",
        )
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a tag."""
    query = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(query)
    tag = result.scalars().first()
    
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Tag not found")

    if tag_data.name is not None and tag_data.name.lower() != tag.name.lower():
        # Check uniqueness if name changed
        dup_query = select(Tag).where(
            Tag.user_id == current_user.id,
            func.lower(Tag.name) == tag_data.name.lower()
        )
        dup_result = await db.execute(dup_query)
        if dup_result.scalars().first():
            raise HTTPException(status_code=400, detail="Tag with this name already exists")
        tag.name = tag_data.name

    if tag_data.color is not None:
        tag.color = tag_data.color

    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a tag."""
    query = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(query)
    tag = result.scalars().first()
    
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Tag not found")

    await db.delete(tag)
    await db.commit()
    return None
