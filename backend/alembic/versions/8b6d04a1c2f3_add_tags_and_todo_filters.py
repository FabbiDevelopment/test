"""Add user tags, todo mappings, and filter indexes.

Revision ID: 8b6d04a1c2f3
Revises: c8f1d2e4a6b0
Create Date: 2026-10-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8b6d04a1c2f3"
down_revision: Union[str, None] = "c8f1d2e4a6b0"
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
    op.create_table(
        "todo_tags",
        sa.Column("todo_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["todo_id"], ["todos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("todo_id", "tag_id"),
    )

    # Concurrent index creation avoids holding a write-blocking table lock
    # while indexing existing todos in production.
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_tags_user_id", "tags", ["user_id"], postgresql_concurrently=True
        )
        op.create_index(
            "uq_tags_user_name_ci",
            "tags",
            ["user_id", sa.text("lower(name)")],
            unique=True,
            postgresql_concurrently=True,
        )
        op.create_index(
            "ix_todo_tags_tag_id",
            "todo_tags",
            ["tag_id"],
            postgresql_concurrently=True,
        )
        op.create_index(
            "ix_todo_tags_todo_id",
            "todo_tags",
            ["todo_id"],
            postgresql_concurrently=True,
        )
        op.create_index(
            "ix_todos_user_completed_created_at_id",
            "todos",
            ["user_id", "completed", "created_at", "id"],
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            "ix_todos_user_completed_created_at_id",
            table_name="todos",
            postgresql_concurrently=True,
        )
        op.drop_index(
            "ix_todo_tags_todo_id",
            table_name="todo_tags",
            postgresql_concurrently=True,
        )
        op.drop_index(
            "ix_todo_tags_tag_id",
            table_name="todo_tags",
            postgresql_concurrently=True,
        )
        op.drop_index(
            "uq_tags_user_name_ci",
            table_name="tags",
            postgresql_concurrently=True,
        )
        op.drop_index(
            "ix_tags_user_id",
            table_name="tags",
            postgresql_concurrently=True,
        )
    op.drop_table("todo_tags")
    op.drop_table("tags")
