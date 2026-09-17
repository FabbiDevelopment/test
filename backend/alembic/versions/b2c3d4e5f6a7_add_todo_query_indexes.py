"""add indexes for todo queries and unique user email

Revision ID: b2c3d4e5f6a7
Revises: a0790c76a129
Create Date: 2026-09-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_todos_user_completed_created",
        "todos",
        ["user_id", "completed", "created_at", "id"],
    )
    op.create_index("uq_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_users_email", table_name="users")
    op.drop_index("ix_todos_user_completed_created", table_name="todos")
