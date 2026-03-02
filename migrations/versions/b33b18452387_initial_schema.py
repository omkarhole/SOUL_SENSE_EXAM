"""Initial schema

Revision ID: b33b18452387
Revises: 
Create Date: 2026-01-07 12:03:39.917326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b33b18452387'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('journal_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('entry_date', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('emotional_patterns', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.Column('last_login', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )

    op.create_table('scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('total_score', sa.Integer(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('detailed_age_group', sa.String(), nullable=True),
        sa.Column('timestamp', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('responses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('question_id', sa.Integer(), nullable=True),
        sa.Column('response_value', sa.Integer(), nullable=True),
        sa.Column('age_group', sa.String(), nullable=True),
        sa.Column('detailed_age_group', sa.String(), nullable=True),
        sa.Column('timestamp', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('question_category',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('question_bank',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=True),
        sa.Column('min_age', sa.Integer(), nullable=True),
        sa.Column('max_age', sa.Integer(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.Column('tooltip', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('question_metadata',
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('tags', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('question_id')
    )

    op.create_table('login_attempts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('is_successful', sa.Boolean(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('statistics_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('stat_name', sa.String(), nullable=True),
        sa.Column('stat_value', sa.Float(), nullable=True),
        sa.Column('stat_json', sa.Text(), nullable=True),
        sa.Column('calculated_at', sa.String(), nullable=True),
        sa.Column('valid_until', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('statistics_cache')
    op.drop_table('login_attempts')
    op.drop_table('question_metadata')
    op.drop_table('question_bank')
    op.drop_table('question_category')
    op.drop_table('responses')
    op.drop_table('scores')
    op.drop_table('users')
    op.drop_table('journal_entries')
