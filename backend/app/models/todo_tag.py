import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.todo import Todo
    from app.models.tag import Tag


class TodoTag(Base):
    """Many-to-many relationship between Todo and Tag."""

    __tablename__ = "todo_tags"

    __table_args__ = (
        Index("ix_todo_tags_tag_id", "tag_id"),
        Index("ix_todo_tags_todo_id", "todo_id"),
    )

    todo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("todos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    todo: Mapped["Todo"] = relationship(
        "Todo",
        back_populates="todo_tags",
    )
    tag: Mapped["Tag"] = relationship(
        "Tag",
        back_populates="todo_tags",
    )
