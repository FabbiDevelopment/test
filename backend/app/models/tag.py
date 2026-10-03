import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, String, func, UniqueConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.todo import Todo
    from app.models.todo_tag import TodoTag


class Tag(Base):
    """Tag model."""

    __tablename__ = "tags"

    __table_args__ = (
        Index("uq_tag_user_id_name_lower", "user_id", text("lower(name)"), unique=True),
        Index("ix_tags_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    color: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="tags",
        lazy="select",
    )
    todo_tags: Mapped[List["TodoTag"]] = relationship(
        "TodoTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )
    todos: Mapped[List["Todo"]] = relationship(
        "Todo",
        secondary="todo_tags",
        back_populates="tags",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"
