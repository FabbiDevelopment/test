"""add_tags_and_todo_tags

Revision ID: 004_tags
Revises: 003_indexes
Create Date: 2026-09-16 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_tags'
down_revision: Union[str, None] = '003_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True, server_default='#6366f1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tags_user_id', 'tags', ['user_id'], unique=False)
    op.create_index(
        'uq_tags_user_id_lower_name',
        'tags',
        ['user_id', sa.text('lower(name)')],
        unique=True,
    )

    # 2. Create todo_tags junction table
    op.create_table(
        'todo_tags',
        sa.Column('todo_id', sa.Uuid(), nullable=False),
        sa.Column('tag_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['todo_id'], ['todos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('todo_id', 'tag_id'),
    )
    op.create_index('ix_todo_tags_todo_id', 'todo_tags', ['todo_id'], unique=False)
    op.create_index('ix_todo_tags_tag_id', 'todo_tags', ['tag_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_todo_tags_tag_id', table_name='todo_tags')
    op.drop_index('ix_todo_tags_todo_id', table_name='todo_tags')
    op.drop_table('todo_tags')
    op.drop_index('uq_tags_user_id_lower_name', table_name='tags')
    op.drop_index('ix_tags_user_id', table_name='tags')
    op.drop_table('tags')
