"""add performance composite indexes

Revision ID: 003_add_performance_indexes
Revises: a0790c76a129
Create Date: 2026-09-19 00:00:00.000000

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
    # 1. Composite index for filtered queries by status and sorting by created_at DESC
    op.create_index(
        "ix_todos_user_id_completed_created_at",
        "todos",
        ["user_id", "completed", sa.text("created_at DESC")],
    )

    # 2. Composite index for default user todo list ordered by created_at DESC
    op.create_index(
        "ix_todos_user_id_created_at",
        "todos",
        ["user_id", sa.text("created_at DESC")],
    )

    # 3. Unique index on user email to optimize authentication and ensure integrity
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_todos_user_id_created_at", table_name="todos")
    op.drop_index("ix_todos_user_id_completed_created_at", table_name="todos")
