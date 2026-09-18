import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.todo import Todo


class Tag(Base):
    """Tag model — per-user, case-insensitive unique name."""

    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship("User", back_populates="tags")
    todo_tags: Mapped[list["TodoTag"]] = relationship(
        "TodoTag", back_populates="tag", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"


class TodoTag(Base):
    """Many-to-many join table between todos and tags."""

    __tablename__ = "todo_tags"

    todo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("todos.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    todo: Mapped["Todo"] = relationship("Todo", back_populates="todo_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="todo_tags")


Index("uq_tags_user_name_ci", Tag.user_id, func.lower(Tag.name), unique=True)
