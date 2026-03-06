"""
Add backfill_jobs table for migration backfill observability.

This migration creates the backfill_jobs table to track all backfill operations
during migrations with metrics, checksums, and rollback capability.
"""

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    """Create backfill_jobs table."""
    op.create_table(
        'backfill_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backfill_id', sa.String(36), nullable=False),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('migration_version', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('records_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('execution_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('success_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('checksum_before', sa.String(64), nullable=True),
        sa.Column('checksum_after', sa.String(64), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('rollback_capable', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('job_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('backfill_id'),
    )
    
    # Create indexes
    op.create_index('idx_backfill_migration_status', 'backfill_jobs', ['migration_version', 'status'])
    op.create_index('idx_backfill_created', 'backfill_jobs', ['created_at'])
    op.create_index('ix_backfill_jobs_backfill_id', 'backfill_jobs', ['backfill_id'])


def downgrade() -> None:
    """Drop backfill_jobs table."""
    op.drop_table('backfill_jobs')
