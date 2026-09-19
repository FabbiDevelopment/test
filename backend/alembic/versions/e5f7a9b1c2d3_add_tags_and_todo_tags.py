"""add tags and todo tag mappings

Revision ID: e5f7a9b1c2d3
Revises: d4e6f8a0b2c3
Create Date: 2026-09-19 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f7a9b1c2d3"
down_revision: Union[str, None] = "d4e6f8a0b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tags_user_id", "tags", ["user_id"], unique=False)
    op.create_index(
        "uq_tags_user_id_lower_name",
        "tags",
        ["user_id", sa.text("lower(name)")],
        unique=True,
    )

    op.create_table(
        "todo_tags",
        sa.Column("todo_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["todo_id"], ["todos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("todo_id", "tag_id"),
    )
    op.create_index("ix_todo_tags_todo_id", "todo_tags", ["todo_id"], unique=False)
    op.create_index("ix_todo_tags_tag_id", "todo_tags", ["tag_id"], unique=False)
    op.create_index(
        "ix_todos_user_id_completed_created_at_id",
        "todos",
        ["user_id", "completed", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_todos_user_id_completed_created_at_id", table_name="todos")
    op.drop_index("ix_todo_tags_tag_id", table_name="todo_tags")
    op.drop_index("ix_todo_tags_todo_id", table_name="todo_tags")
    op.drop_table("todo_tags")
    op.drop_index("uq_tags_user_id_lower_name", table_name="tags")
    op.drop_index("ix_tags_user_id", table_name="tags")
    op.drop_table("tags")
