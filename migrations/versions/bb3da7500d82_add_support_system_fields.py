"""Add support system fields to personal_profiles

Revision ID: bb3da7500d82
Revises: f62984ab805f
Create Date: 2026-02-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb3da7500d82'
down_revision: Union[str, Sequence[str], None] = 'f62984ab805f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add support system fields to personal_profiles."""
    with op.batch_alter_table('personal_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('has_therapist', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('support_network_size', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('primary_support_type', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('sleep_hours', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove support system fields from personal_profiles."""
    with op.batch_alter_table('personal_profiles', schema=None) as batch_op:
        batch_op.drop_column('has_therapist')
        batch_op.drop_column('support_network_size')
        batch_op.drop_column('primary_support_type')
        batch_op.drop_column('sleep_hours')