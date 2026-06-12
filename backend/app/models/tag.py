import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.todo import Todo


class TodoTag(Base):
    __tablename__ = "todo_tags"

    todo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("todos.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        Index("ix_todo_tags_todo_id", "todo_id"),
        Index("ix_todo_tags_tag_id", "tag_id"),
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_tags_user_id", "user_id"),
        Index("uix_tags_user_id_lower_name", "user_id", text("lower(name)"), unique=True),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tags", lazy="select")
    todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        secondary="todo_tags",
        back_populates="tags",
        lazy="select",
    )
