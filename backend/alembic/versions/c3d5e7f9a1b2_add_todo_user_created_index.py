"""add todo user and creation order index

Revision ID: c3d5e7f9a1b2
Revises: a0790c76a129
Create Date: 2026-09-18 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3d5e7f9a1b2"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEX_NAME = "ix_todos_user_id_created_at_id"


def upgrade() -> None:
    # CONCURRENTLY avoids blocking writes while PostgreSQL scans a large table.
    with op.get_context().autocommit_block():
        op.create_index(
            INDEX_NAME,
            "todos",
            ["user_id", "created_at", "id"],
            unique=False,
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            INDEX_NAME,
            table_name="todos",
            postgresql_concurrently=True,
        )
