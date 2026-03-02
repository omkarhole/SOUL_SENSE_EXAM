"""normalize_score_response_user_id_fk

Revision ID: 20260227102116
Revises: 679f6276cf18
Create Date: 2026-02-27 10:21:16.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260227102116'
down_revision: Union[str, Sequence[str], None] = '679f6276cf18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Remove redundant user_id FK from scores and responses tables.

    User information can be accessed via JOIN through user_sessions table using session_id.
    """

    # Remove user_id column and its index from scores table
    with op.batch_alter_table('scores', schema=None) as batch_op:
        batch_op.drop_index('idx_score_user_timestamp')
        batch_op.drop_column('user_id')

    # Remove user_id column and its index from responses table
    with op.batch_alter_table('responses', schema=None) as batch_op:
        batch_op.drop_index('idx_response_user_timestamp')
        batch_op.drop_column('user_id')


def downgrade() -> None:
    """Downgrade schema: Restore user_id FK to scores and responses tables."""

    # Add back user_id column to scores table
    with op.batch_alter_table('scores', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
        batch_op.create_index('idx_score_user_timestamp', ['user_id', 'timestamp'], unique=False)

    # Add back user_id column to responses table
    with op.batch_alter_table('responses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
        batch_op.create_index('idx_response_user_timestamp', ['user_id', 'timestamp'], unique=False)