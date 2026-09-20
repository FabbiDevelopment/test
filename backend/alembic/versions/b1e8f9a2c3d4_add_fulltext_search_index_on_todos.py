"""add_fulltext_search_index_on_todos

Revision ID: b1e8f9a2c3d4
Revises: fa4ce20558c6
Create Date: 2026-09-20 09:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1e8f9a2c3d4'
down_revision: Union[str, None] = 'fa4ce20558c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Clean up any previous fts index if exists
    op.execute(sa.text("DROP INDEX IF EXISTS ix_todos_fts"))

    # 2. Enable pg_trgm extension for high-performance substring/ILIKE search
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

    # 3. Create GIN Trigram indexes on title and description
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_todos_title_trgm "
            "ON todos USING gin (title gin_trgm_ops)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_todos_description_trgm "
            "ON todos USING gin (description gin_trgm_ops)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_todos_description_trgm"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_todos_title_trgm"))

