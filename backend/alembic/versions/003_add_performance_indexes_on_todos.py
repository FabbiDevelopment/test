"""add_performance_indexes_on_todos

Revision ID: 003_indexes
Revises: a0790c76a129
Create Date: 2026-09-16 17:09:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_indexes'
down_revision: Union[str, None] = 'a0790c76a129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Composite index for user pagination: WHERE user_id = :uid ORDER BY created_at DESC, id DESC
    op.create_index(
        'ix_todos_user_id_created_at',
        'todos',
        ['user_id', sa.text('created_at DESC'), sa.text('id DESC')],
        unique=False,
    )

    # 2. Composite index for filtered queries: WHERE user_id = :uid AND completed = :bool ORDER BY created_at DESC
    op.create_index(
        'ix_todos_user_completed_created_at',
        'todos',
        ['user_id', 'completed', sa.text('created_at DESC')],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_todos_user_completed_created_at', table_name='todos')
    op.drop_index('ix_todos_user_id_created_at', table_name='todos')
