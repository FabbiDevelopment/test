"""create_tags_and_todo_tags_tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-20 22:00:00.000000

Tier 4: Create tags and todo_tags tables, unique constraint on user_id + lower(name),
and performance indexes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 2. Case-insensitive unique constraint on (user_id, lower(name))
    op.create_index(
        'uq_tags_user_lower_name',
        'tags',
        ['user_id', sa.text('lower(name)')],
        unique=True
    )
    
    # Index on tags(user_id)
    op.create_index('idx_tags_user_id', 'tags', ['user_id'])

    # 3. Create todo_tags junction table
    op.create_table(
        'todo_tags',
        sa.Column('todo_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['todo_id'], ['todos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('todo_id', 'tag_id')
    )

    # Indexes on todo_tags
    op.create_index('idx_todo_tags_todo_id', 'todo_tags', ['todo_id'])
    op.create_index('idx_todo_tags_tag_id', 'todo_tags', ['tag_id'])


def downgrade() -> None:
    op.drop_index('idx_todo_tags_tag_id', table_name='todo_tags')
    op.drop_index('idx_todo_tags_todo_id', table_name='todo_tags')
    op.drop_table('todo_tags')
    op.drop_index('idx_tags_user_id', table_name='tags')
    op.drop_index('uq_tags_user_lower_name', table_name='tags')
    op.drop_table('tags')
