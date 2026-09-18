"""add composite index on todos(user_id, completed, created_at)

Revision ID: b3f7c9a21d44
Revises: a0790c76a129
Create Date: 2026-09-17 10:00:00.000000

Every todo list query the app runs (GET /todos list, count, and the
common "only show incomplete" filter) filters by user_id, optionally
by completed, and orders by created_at DESC. Before this migration the
only index on `todos` is the primary key on `id`, so every one of
those queries does a full sequential scan.

Benchmarked before/after on a seeded table of 1,000,000 todos /
10,000 users (see docs/DB_PERFORMANCE.md for the full EXPLAIN ANALYZE
output and rationale): ~110-121ms sequential scans dropped to
sub-millisecond index-only/index scans.

Uses CREATE INDEX CONCURRENTLY (via Alembic's autocommit_block) so
this migration does not hold a table-level lock that blocks writes on
`todos` for its duration - important since this table is expected to
be large in production. CONCURRENTLY cannot run inside a transaction,
which is why upgrade()/downgrade() use autocommit_block() instead of
Alembic's default per-migration transaction.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3f7c9a21d44"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "ix_todos_user_id_completed_created_at"


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            INDEX_NAME,
            "todos",
            ["user_id", "completed", "created_at"],
            unique=False,
            postgresql_concurrently=True,
            if_not_exists=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            INDEX_NAME,
            table_name="todos",
            postgresql_concurrently=True,
            if_exists=True,
        )
