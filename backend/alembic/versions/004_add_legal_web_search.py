"""add legal_web_search table

Revision ID: 004
Revises: 003
Create Date: 2026-03-24 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'legal_web_search',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('query', sa.String(length=1024), nullable=False),
        sa.Column('results', sa.JSON, nullable=False),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_legalweb_tenant_query', 'legal_web_search', ['tenant_id', 'query'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_legalweb_tenant_query', table_name='legal_web_search')
    op.drop_table('legal_web_search')
