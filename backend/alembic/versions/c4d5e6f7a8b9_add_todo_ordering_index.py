"""add todo ordering index

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-09-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_todos_user_created_id",
        "todos",
        ["user_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_todos_user_created_id", table_name="todos")
