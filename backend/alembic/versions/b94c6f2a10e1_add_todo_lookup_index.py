"""add index for user todo listing and counting

Revision ID: b94c6f2a10e1
Revises: a0790c76a129
Create Date: 2026-09-17 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b94c6f2a10e1"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "ix_todos_user_created_at_id"


def upgrade() -> None:
    # CONCURRENTLY avoids blocking writes while PostgreSQL scans a large table.
    # It cannot run inside Alembic's normal migration transaction.
    with op.get_context().autocommit_block():
        op.create_index(
            INDEX_NAME,
            "todos",
            ["user_id", sa.text("created_at DESC"), sa.text("id DESC")],
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
