"""Add missing contract status values

Revision ID: 003
Revises: 002
Create Date: 2026-03-23 22:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, Sequence[str], None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add missing 'analyzing' and 'analysis_failed' statuses to contractstatus enum."""
    # PostgreSQL doesn't support direct enum modification, so we need to alter the type
    # Add 'analyzing' before 'analyzed' for logical ordering
    op.execute(
        "ALTER TYPE contractstatus ADD VALUE 'analyzing' BEFORE 'analyzed'"
    )
    
    # Add 'analysis_failed' after 'analyzing'
    op.execute(
        "ALTER TYPE contractstatus ADD VALUE 'analysis_failed' AFTER 'analyzing'"
    )


def downgrade() -> None:
    """Downgrade schema - Remove 'analyzing' and 'analysis_failed' statuses."""
    # PostgreSQL doesn't support removing enum values, so we'll keep them
    # This is a limitation of PostgreSQL enums - they can't be removed once added
    # The workaround is to recreate the enum type entirely if rollback is needed
    pass
