"""Merge multiple heads

Revision ID: 51f39ae2a4d0
Revises: bb3da7500d82, c0d9a527bd0e, d108d0b41e08
Create Date: 2026-02-26 13:29:17.358176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51f39ae2a4d0'
down_revision: Union[str, Sequence[str], None] = ('bb3da7500d82', 'c0d9a527bd0e', 'd108d0b41e08')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
