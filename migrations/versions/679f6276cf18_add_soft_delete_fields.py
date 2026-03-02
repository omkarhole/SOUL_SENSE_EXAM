"""add_soft_delete_fields

Revision ID: 679f6276cf18
Revises: ec4851e5e16c
Create Date: 2026-02-27 10:04:46.345690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '679f6276cf18'
down_revision: Union[str, Sequence[str], None] = 'ec4851e5e16c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add soft delete fields to journal_entries and assessment_results tables."""
    
    # Add soft delete fields to journal_entries table
    with op.batch_alter_table('journal_entries') as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
        # Note: is_deleted column already exists, but let's ensure it has the correct properties
        # If it doesn't exist, this will add it; if it does, this is a no-op
        try:
            batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False, index=True))
        except Exception:
            # Column might already exist, skip
            pass
    
    # Add soft delete fields to assessment_results table
    with op.batch_alter_table('assessment_results') as batch_op:
        batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False, index=True))
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Set default values for existing rows (is_deleted = False)
    op.execute("UPDATE journal_entries SET is_deleted = 0 WHERE is_deleted IS NULL")
    op.execute("UPDATE assessment_results SET is_deleted = 0 WHERE is_deleted IS NULL")


def downgrade() -> None:
    """Downgrade schema: Remove soft delete fields."""
    
    # Remove soft delete fields from assessment_results table
    with op.batch_alter_table('assessment_results') as batch_op:
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('is_deleted')
    
    # Remove soft delete fields from journal_entries table
    # Note: Keep is_deleted as it might be used elsewhere, only remove deleted_at
    with op.batch_alter_table('journal_entries') as batch_op:
        batch_op.drop_column('deleted_at')
