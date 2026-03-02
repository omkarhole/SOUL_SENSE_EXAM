"""Enhance audit logs schema for comprehensive security monitoring

Revision ID: c0d9a527bd0e
Revises: e4f5a6b7c8d9
Create Date: 2026-02-25 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0d9a527bd0e'
down_revision: Union[str, Sequence[str], None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enhance audit_logs table for comprehensive security monitoring."""
    # Add new columns to audit_logs table
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        # Add event_id column (UUID for uniqueness)
        batch_op.add_column(sa.Column('event_id', sa.String(36), nullable=True))
        batch_op.create_index('ix_audit_logs_event_id', ['event_id'], unique=True)

        # Add event categorization columns
        batch_op.add_column(sa.Column('event_type', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('severity', sa.String(20), server_default='info', nullable=True))

        # Add username column for better querying
        batch_op.add_column(sa.Column('username', sa.String(100), nullable=True))

        # Add resource tracking columns
        batch_op.add_column(sa.Column('resource_type', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('resource_id', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('action', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('outcome', sa.String(20), server_default='success', nullable=True))

        # Add additional metadata columns
        batch_op.add_column(sa.Column('details', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))

        # Add compliance and retention columns
        batch_op.add_column(sa.Column('retention_until', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('archived', sa.Boolean(), server_default='0', nullable=True))

    # Create indexes for better query performance
    op.create_index('ix_audit_logs_timestamp_event_type', 'audit_logs', ['timestamp', 'event_type'], unique=False)
    op.create_index('ix_audit_logs_user_timestamp', 'audit_logs', ['user_id', 'timestamp'], unique=False)
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'], unique=False)
    op.create_index('ix_audit_logs_username', 'audit_logs', ['username'], unique=False)
    op.create_index('ix_audit_logs_event_type', 'audit_logs', ['event_type'], unique=False)
    op.create_index('ix_audit_logs_severity', 'audit_logs', ['severity'], unique=False)

    # Update existing records to have default values
    # Set event_type based on existing action patterns
    op.execute("""
        UPDATE audit_logs
        SET event_type = CASE
            WHEN action IN ('LOGIN', 'PASSWORD_CHANGE', '2FA_ENABLE', 'LOGOUT') THEN 'auth'
            WHEN action LIKE '%EXPORT%' OR action LIKE '%BACKUP%' THEN 'data_access'
            WHEN action LIKE '%ADMIN%' OR action LIKE '%CONFIG%' THEN 'admin'
            ELSE 'system'
        END
        WHERE event_type IS NULL
    """)

    # Set outcome based on action content
    op.execute("""
        UPDATE audit_logs
        SET outcome = CASE
            WHEN action LIKE '%FAIL%' OR action LIKE '%ERROR%' THEN 'failure'
            ELSE 'success'
        END
        WHERE outcome IS NULL
    """)

    # Set severity based on event type and outcome
    op.execute("""
        UPDATE audit_logs
        SET severity = CASE
            WHEN outcome = 'failure' THEN 'warning'
            WHEN event_type = 'admin' THEN 'warning'
            ELSE 'info'
        END
        WHERE severity IS NULL
    """)

    # Generate event_ids for existing records
    op.execute("""
        UPDATE audit_logs
        SET event_id = LOWER(HEX(RANDOM_UUID()))
        WHERE event_id IS NULL
    """)

    # Set retention dates for existing records (90 days from now)
    op.execute("""
        UPDATE audit_logs
        SET retention_until = DATETIME('now', '+90 days')
        WHERE retention_until IS NULL
    """)


def downgrade() -> None:
    """Revert audit_logs table enhancements."""
    # Drop indexes
    op.drop_index('ix_audit_logs_severity', table_name='audit_logs')
    op.drop_index('ix_audit_logs_event_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_username', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_timestamp_event_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_event_id', table_name='audit_logs')

    # Drop new columns
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.drop_column('archived')
        batch_op.drop_column('retention_until')
        batch_op.drop_column('error_message')
        batch_op.drop_column('details')
        batch_op.drop_column('outcome')
        batch_op.drop_column('action')
        batch_op.drop_column('resource_id')
        batch_op.drop_column('resource_type')
        batch_op.drop_column('username')
        batch_op.drop_column('severity')
        batch_op.drop_column('event_type')
        batch_op.drop_column('event_id')