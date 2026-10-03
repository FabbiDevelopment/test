"""add index on user_id, completed, created_at in todos

Revision ID: 96504b13d1bd
Revises: a0790c76a129
Create Date: 2026-10-03 05:22:18.708517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96504b13d1bd'
down_revision: Union[str, None] = 'a0790c76a129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_todos_user_id_completed_created_at', 'todos', ['user_id', 'completed', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_todos_user_id_completed_created_at', table_name='todos')
