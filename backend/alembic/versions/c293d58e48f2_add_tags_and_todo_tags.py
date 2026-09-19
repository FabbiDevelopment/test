"""add_tags_and_todo_tags

Revision ID: c293d58e48f2
Revises: b182c49a37e1
Create Date: 2026-09-19 19:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c293d58e48f2'
down_revision: Union[str, None] = 'b182c49a37e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_tag_name'),
    )
    op.create_index('ix_tags_user_id', 'tags', ['user_id'], unique=False)

    # Create todo_tags association table
    op.create_table(
        'todo_tags',
        sa.Column('todo_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['todo_id'], ['todos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('todo_id', 'tag_id'),
    )
    op.create_index('ix_todo_tags_tag_id', 'todo_tags', ['tag_id'], unique=False)
    op.create_index('ix_todo_tags_todo_id', 'todo_tags', ['todo_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_todo_tags_todo_id', table_name='todo_tags')
    op.drop_index('ix_todo_tags_tag_id', table_name='todo_tags')
    op.drop_table('todo_tags')
    op.drop_index('ix_tags_user_id', table_name='tags')
    op.drop_table('tags')
