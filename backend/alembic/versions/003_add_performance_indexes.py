"""add_performance_indexes

Revision ID: 003_add_performance_indexes
Revises: a0790c76a129
Create Date: 2026-09-22 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_add_performance_indexes"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Composite index for filtering by user, status, and ordering by created_at
    op.create_index(
        "idx_todos_user_completed_created",
        "todos",
        ["user_id", "completed", "created_at"],
        unique=False,
    )

    # 2. Composite index for user todos ordered by created_at (without status filter)
    op.create_index(
        "idx_todos_user_created",
        "todos",
        ["user_id", "created_at"],
        unique=False,
    )

    # 3. Unique index on users(email) to prevent sequential scan during login/register
    op.create_index(
        "idx_users_email",
        "users",
        ["email"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_users_email", table_name="users")
    op.drop_index("idx_todos_user_created", table_name="todos")
    op.drop_index("idx_todos_user_completed_created", table_name="todos")
