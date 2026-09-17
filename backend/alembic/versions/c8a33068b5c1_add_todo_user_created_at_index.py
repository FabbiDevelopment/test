"""add todo user created at index

Revision ID: c8a33068b5c1
Revises: a0790c76a129
Create Date: 2026-09-17 21:36:52.381980

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c8a33068b5c1'
down_revision: Union[str, None] = 'a0790c76a129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_todos_user_id_created_at",
            "todos",
            ["user_id", "created_at"],
            unique=False,
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            "ix_todos_user_id_created_at",
            table_name="todos",
            postgresql_concurrently=True,
        )
