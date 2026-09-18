"""add indexes for todo list queries

Revision ID: b1a2c3d4e5f6
Revises: a0790c76a129
Create Date: 2026-09-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b1a2c3d4e5f6"
down_revision = "a0790c76a129"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("uq_users_email", "users", ["email"], unique=True)
    op.create_index(
        "ix_todos_user_created_id",
        "todos",
        ["user_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )
    op.create_index(
        "ix_todos_user_completed_created",
        "todos",
        ["user_id", "completed", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_todos_user_completed_created", table_name="todos")
    op.drop_index("ix_todos_user_created_id", table_name="todos")
    op.drop_index("uq_users_email", table_name="users")
