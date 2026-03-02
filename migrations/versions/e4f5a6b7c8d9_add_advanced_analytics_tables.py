"""Add advanced analytics tables for emotional pattern recognition

Revision ID: e4f5a6b7c8d9
Revises: a7b8c9d0e1f2
Create Date: 2026-02-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add advanced analytics tables for Feature #804."""

    # Emotional Patterns Table
    op.create_table('emotional_patterns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('pattern_type', sa.String(), nullable=False),
        sa.Column('pattern_data', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('emotional_patterns', schema=None) as batch_op:
        batch_op.create_index('idx_emotional_patterns_user_type', ['username', 'pattern_type'], unique=False)
        batch_op.create_index('idx_emotional_patterns_detected', ['detected_at'], unique=False)

    # User Benchmarks Table
    op.create_table('user_benchmarks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('benchmark_type', sa.String(), nullable=False),
        sa.Column('percentile', sa.Integer(), nullable=False),
        sa.Column('comparison_group', sa.String(), nullable=False),
        sa.Column('benchmark_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user_benchmarks', schema=None) as batch_op:
        batch_op.create_index('idx_user_benchmarks_user_type', ['username', 'benchmark_type'], unique=False)
        batch_op.create_index('idx_user_benchmarks_created', ['created_at'], unique=False)

    # Analytics Insights Table
    op.create_table('analytics_insights',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('insight_type', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('priority', sa.String(), nullable=True),
        sa.Column('insight_data', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('analytics_insights', schema=None) as batch_op:
        batch_op.create_index('idx_analytics_insights_user_type', ['username', 'insight_type'], unique=False)
        batch_op.create_index('idx_analytics_insights_created', ['created_at'], unique=False)

    # Mood Forecasts Table
    op.create_table('mood_forecasts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('forecast_date', sa.DateTime(), nullable=False),
        sa.Column('predicted_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('forecast_basis', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('mood_forecasts', schema=None) as batch_op:
        batch_op.create_index('idx_mood_forecasts_user_date', ['username', 'forecast_date'], unique=False)
        batch_op.create_index('idx_mood_forecasts_created', ['created_at'], unique=False)


def downgrade() -> None:
    """Remove advanced analytics tables."""

    # Drop tables in reverse order
    op.drop_table('mood_forecasts')
    op.drop_table('analytics_insights')
    op.drop_table('user_benchmarks')
    op.drop_table('emotional_patterns')