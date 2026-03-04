"""Add constraint for answer scale

Revision ID: d108d0b41e08
Revises: a7b8c9d0e1f2
Create Date: 2026-02-23 20:52:04.148582

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd108d0b41e08'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Clean up legacy data that violates the new constraint
    op.execute("UPDATE responses SET response_value = 3 WHERE response_value IS NULL OR response_value < 1")
    op.execute("UPDATE responses SET response_value = 5 WHERE response_value > 5")
    
    # Add check constraint to enforce 1-5 scale
    op.create_check_constraint('ck_response_value_range', 'responses', 'response_value >= 1 AND response_value <= 5')


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the check constraint
    op.drop_constraint('ck_response_value_range', 'responses', type_='check')
