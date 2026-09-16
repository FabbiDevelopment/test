import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Tag(Base):
    """Tag model — nhãn gắn vào todo, scoped per user."""

    __tablename__ = "tags"
    __table_args__ = (
        # THÊM: unique tag name per user (case-insensitive enforced at service layer)
        UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
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

    user: Mapped["User"] = relationship("User", back_populates="tags", lazy="select")
    todo_tags: Mapped[list["TodoTag"]] = relationship(
        "TodoTag", back_populates="tag", cascade="all, delete-orphan"
    )


class TodoTag(Base):
    """Association table — many-to-many todos ↔ tags."""

    __tablename__ = "todo_tags"

    todo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("todos.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )

    tag: Mapped["Tag"] = relationship("Tag", back_populates="todo_tags")
