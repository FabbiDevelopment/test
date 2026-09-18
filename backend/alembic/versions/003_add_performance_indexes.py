"""Indexes for user todo queries and login lookup.

Revision ID: 003_add_performance_indexes
Revises: a0790c76a129
"""
from alembic import op
import sqlalchemy as sa

revision = "003_add_performance_indexes"
down_revision = "a0790c76a129"
branch_labels = None
depends_on = None

def upgrade():
    op.create_index(
        "idx_todos_user_completed_created",
        "todos",
        ["user_id", "completed", sa.text("created_at DESC"), sa.text("id DESC")],
    )
    op.create_index("idx_users_email_unique", "users", ["email"], unique=True)


def downgrade():
    op.drop_index("idx_users_email_unique", table_name="users")
    op.drop_index("idx_todos_user_completed_created", table_name="todos")
