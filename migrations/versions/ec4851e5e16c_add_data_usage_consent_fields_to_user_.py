"""Add data usage consent fields to user_settings

Revision ID: ec4851e5e16c
Revises: 51f39ae2a4d0
Create Date: 2026-02-26 13:29:21.707832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec4851e5e16c'
down_revision: Union[str, Sequence[str], None] = '51f39ae2a4d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add data usage consent fields to user_settings table
    with op.batch_alter_table('user_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('consent_ml_training', sa.Boolean(), nullable=False, default=False))
        batch_op.add_column(sa.Column('consent_aggregated_research', sa.Boolean(), nullable=False, default=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove data usage consent fields from user_settings table
    with op.batch_alter_table('user_settings', schema=None) as batch_op:
        batch_op.drop_column('consent_aggregated_research')
        batch_op.drop_column('consent_ml_training')
