"""add_unique_constraint_on_users_email

Revision ID: b1c2d3e4f5a6
Revises: a0790c76a129
Create Date: 2026-09-19 10:48:00.000000

Bug #9 fix: Add unique constraint on users.email to enforce uniqueness at the
database level, preventing duplicate accounts via race conditions or direct
DB inserts even when application-level checks pass concurrently.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a0790c76a129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint on users.email
    op.create_unique_constraint(
        'uq_users_email',
        'users',
        ['email'],
    )


def downgrade() -> None:
    # Remove unique constraint on users.email
    op.drop_constraint(
        'uq_users_email',
        'users',
        type_='unique',
    )
