"""enforce unique user email addresses

Revision ID: d4e6f8a0b2c3
Revises: c3d5e7f9a1b2
Create Date: 2026-09-18 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e6f8a0b2c3"
down_revision: Union[str, None] = "c3d5e7f9a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONSTRAINT_NAME = "uq_users_email"


def upgrade() -> None:
    duplicate = op.get_bind().execute(
        sa.text(
            "SELECT 1 FROM users GROUP BY email HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).scalar_one_or_none()
    if duplicate:
        raise RuntimeError(
            "Cannot add unique users.email constraint while duplicate emails exist"
        )
    op.create_unique_constraint(CONSTRAINT_NAME, "users", ["email"])


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "users", type_="unique")
