import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TodoTag(Base):
    
    __tablename__ = "todo_tags"

    # ID Todo (
    todo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("todos.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    # ID Tag 
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
