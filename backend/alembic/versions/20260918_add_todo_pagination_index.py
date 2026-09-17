"""add composite todo pagination index

Revision ID: 20260918_todo_pagination
Revises: 20260918_query_indexes
Create Date: 2026-09-18 03:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260918_todo_pagination"
down_revision: Union[str, None] = "20260918_query_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_todos_user_id", table_name="todos")
    op.create_index(
        "ix_todos_user_created_at",
        "todos",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_todos_user_created_at", table_name="todos")
    op.create_index("ix_todos_user_id", "todos", ["user_id"])
