"""add_todos_composite_index

Revision ID: b1029c87d234
Revises: a0790c76a129
Create Date: 2026-10-03 07:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1029c87d234'
down_revision: Union[str, None] = 'a0790c76a129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create composite indexes to optimize user todo filtering, status filtering, and created_at sorting
    op.create_index(
        'ix_todos_user_id_completed_created_at',
        'todos',
        ['user_id', 'completed', 'created_at'],
        unique=False,
    )
    op.create_index(
        'ix_todos_user_id_created_at',
        'todos',
        ['user_id', 'created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_todos_user_id_created_at', table_name='todos')
    op.drop_index('ix_todos_user_id_completed_created_at', table_name='todos')
