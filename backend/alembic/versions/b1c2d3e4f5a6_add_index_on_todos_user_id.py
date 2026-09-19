"""add_index_on_todos_user_id

Revision ID: b1c2d3e4f5a6
Revises: a0790c76a129
Create Date: 2026-09-19 00:23:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a0790c76a129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_todos_user_id",
        "todos",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_todos_user_id", table_name="todos")
