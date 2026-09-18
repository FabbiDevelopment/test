"""add todo query indexes

Revision ID: c41f86a92d10
Revises: a0790c76a129
Create Date: 2026-09-18 17:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c41f86a92d10"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CONCURRENTLY avoids blocking writes while PostgreSQL scans a large table.
    # It cannot run inside Alembic's normal migration transaction.
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_todos_user_created_id",
            "todos",
            ["user_id", sa.text("created_at DESC"), sa.text("id DESC")],
            unique=False,
            postgresql_concurrently=True,
        )
        op.create_index(
            "ix_todos_user_completed_created_id",
            "todos",
            [
                "user_id",
                "completed",
                sa.text("created_at DESC"),
                sa.text("id DESC"),
            ],
            unique=False,
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            "ix_todos_user_completed_created_id",
            table_name="todos",
            postgresql_concurrently=True,
        )
        op.drop_index(
            "ix_todos_user_created_id",
            table_name="todos",
            postgresql_concurrently=True,
        )
