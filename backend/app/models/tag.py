import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.todo import Todo
    from app.models.user import User


class Tag(Base):
    __tablename__ = "tags"

    # Khóa chính UUID
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # Khóa ngoại liên kết tới người sở hữu tag 
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tên Tag
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Mã màu 
    color: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )


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

    # Quan hệ manytoOne User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="tags",
    )

    # Quan hệ ManyToMany Tag
    todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        secondary="todo_tags",
        back_populates="tags",
    )

    __table_args__ = (
        Index("uq_tags_user_lower_name", "user_id", func.lower(name), unique=True),
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"
