"""add_composite_index_on_todos

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-09-19 16:50:00.000000

Task 3C: Add composite B-tree index on todos(user_id, completed, created_at DESC)
to optimize user-filtered todo queries, completion state filtering, and ordering.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create composite B-tree index on todos table
    op.create_index(
        'idx_todos_user_completed_created',
        'todos',
        ['user_id', 'completed', sa.text('created_at DESC')],
        unique=False,
    )


def downgrade() -> None:
    # Drop composite index
    op.drop_index(
        'idx_todos_user_completed_created',
        table_name='todos',
    )
