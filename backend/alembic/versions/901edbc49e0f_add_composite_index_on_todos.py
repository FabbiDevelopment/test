"""add_composite_index_on_todos

Revision ID: 901edbc49e0f
Revises: a0790c76a129
Create Date: 2026-09-19 18:08:47.406549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '901edbc49e0f'
down_revision: Union[str, None] = 'a0790c76a129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_todos_user_completed_created',
        'todos',
        ['user_id', 'completed', 'created_at'],
        unique=False,
    )
    op.create_index(
        'ix_todos_user_created',
        'todos',
        ['user_id', 'created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_todos_user_created', table_name='todos')
    op.drop_index('ix_todos_user_completed_created', table_name='todos')
