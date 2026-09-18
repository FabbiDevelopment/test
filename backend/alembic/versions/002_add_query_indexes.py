"""add user email and todo list indexes

Revision ID: 002_add_query_indexes
Revises: a0790c76a129
Create Date: 2026-09-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "002_add_query_indexes"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("uq_users_email", "users", ["email"], unique=True)
    op.create_index(
        "ix_todos_user_created_id",
        "todos",
        ["user_id", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_todos_user_created_id", table_name="todos")
    op.drop_index("uq_users_email", table_name="users")
