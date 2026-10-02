"""Database model and association table for todo tags."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

todo_tags = Table(
    "todo_tags",
    Base.metadata,
    Column(
        "todo_id",
        Uuid(as_uuid=True),
        ForeignKey("todos.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Uuid(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
# Associates todos with tags through a many-to-many relationship.


class Tag(Base):
    """A user-owned label that can be attached to multiple todos."""

    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="tags", lazy="select")
    todos = relationship(
        "Todo",
        secondary=todo_tags,
        back_populates="tags",
        lazy="selectin",
    )


Index("ix_tags_user_id", Tag.user_id)
Index(
    "uq_tags_user_name_ci",
    Tag.user_id,
    func.lower(Tag.name),
    unique=True,
)
