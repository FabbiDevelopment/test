"""add_todos_composite_index

Revision ID: b1880c76a130
Revises: a0790c76a129
Create Date: 2026-09-15 14:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1880c76a130'
down_revision: Union[str, None] = 'a0790c76a129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_todos_user_completed_created',
        'todos',
        ['user_id', 'completed', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_todos_user_completed_created', table_name='todos')
