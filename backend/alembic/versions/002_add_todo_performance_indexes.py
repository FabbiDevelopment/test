"""Add performance indexes on todos table

Revision ID: 002_perf_indexes
Revises: a0790c76a129
Create Date: 2026-09-16

THÊM: Composite index (user_id, completed, created_at) — tối ưu list/filter/count queries.
Level 3C — Database performance optimization via Alembic migration.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002_perf_indexes"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SAI (trước migration): không có index trên user_id → Seq Scan trên bảng lớn (1M+ rows)
    # THÊM: composite index phục vụ 3 query patterns chính:
    #   1. WHERE user_id = ? ORDER BY created_at DESC  (list todos)
    #   2. WHERE user_id = ? AND completed = ?         (filter by status)
    #   3. SELECT COUNT(*) WHERE user_id = ?             (pagination total)
    op.create_index(
        "ix_todos_user_completed_created",
        "todos",
        ["user_id", "completed", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_todos_user_id",
        "todos",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_todos_user_id", table_name="todos")
    op.drop_index("ix_todos_user_completed_created", table_name="todos")
