"""Add index for user-scoped todo listing and counts.

Revision ID: c8f1d2e4a6b0
Revises: a0790c76a129
Create Date: 2026-10-02
"""
from typing import Sequence, Union

from alembic import op


revision: str = "c8f1d2e4a6b0"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Concurrent creation avoids blocking todo reads/writes for the duration
    # of the index build on a populated production table.
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_todos_user_created_at_id",
            "todos",
            ["user_id", "created_at", "id"],
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            "ix_todos_user_created_at_id",
            table_name="todos",
            postgresql_concurrently=True,
        )
