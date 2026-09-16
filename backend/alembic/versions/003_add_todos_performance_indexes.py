"""add_todos_performance_indexes

Revision ID: 003_perf_indexes
Revises: a0790c76a129
Create Date: 2026-09-16 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_perf_indexes'
down_revision: Union[str, None] = 'a0790c76a129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Composite index for user todos ordered by created_at DESC
    # Covers: SELECT * FROM todos WHERE user_id = :uid ORDER BY created_at DESC LIMIT :limit
    # and: SELECT count(*) FROM todos WHERE user_id = :uid (Index-Only Scan)
    op.create_index(
        'ix_todos_user_id_created_at',
        'todos',
        ['user_id', sa.text('created_at DESC')],
        unique=False,
    )

    # 2. Composite index for user todos filtered by completion status and ordered by created_at DESC
    # Covers: SELECT * FROM todos WHERE user_id = :uid AND completed = :completed ORDER BY created_at DESC
    op.create_index(
        'ix_todos_user_id_completed_created_at',
        'todos',
        ['user_id', 'completed', sa.text('created_at DESC')],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_todos_user_id_completed_created_at', table_name='todos')
    op.drop_index('ix_todos_user_id_created_at', table_name='todos')
