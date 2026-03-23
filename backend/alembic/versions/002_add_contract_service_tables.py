"""Add Contract Service tables

Revision ID: 002
Revises: 001
Create Date: 2026-03-23 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, Sequence[str], None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add Contract and Clause tables for Contract Service."""
    # Create ENUM types if they don't exist
    contractstatus_enum = postgresql.ENUM(
        'uploaded', 'processing', 'analyzed', 'review_pending', 'approved', 'rejected', 'archived',
        name='contractstatus'
    )
    contractstatus_enum.create(op.get_bind(), checkfirst=True)
    
    clauseseverity_enum = postgresql.ENUM(
        'critical', 'high', 'medium', 'low', 'info',
        name='clauseseverity'
    )
    clauseseverity_enum.create(op.get_bind(), checkfirst=True)
    
    # Create contracts table
    op.create_table(
        'contracts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('uploaded_by', sa.UUID(), nullable=False),
        sa.Column('filename', sa.VARCHAR(length=255), nullable=False),
        sa.Column('counterparty_name', sa.VARCHAR(length=255), nullable=True),
        sa.Column('contract_type', sa.VARCHAR(length=100), nullable=True),
        sa.Column('file_path', sa.VARCHAR(length=500), nullable=False),
        sa.Column('raw_text', sa.TEXT(), nullable=True),
        sa.Column('text_extraction_confidence', sa.INTEGER(), nullable=True),
        sa.Column('status', postgresql.ENUM('uploaded', 'processing', 'analyzed', 'review_pending', 'approved', 'rejected', 'archived', name='contractstatus', create_type=False), nullable=False, server_default='uploaded'),
        sa.Column('analysis_job_id', sa.VARCHAR(length=255), nullable=True),
        sa.Column('overall_risk_score', sa.INTEGER(), nullable=True),
        sa.Column('total_clauses_found', sa.INTEGER(), nullable=False, server_default='0'),
        sa.Column('critical_issues', sa.INTEGER(), nullable=False, server_default='0'),
        sa.Column('high_issues', sa.INTEGER(), nullable=False, server_default='0'),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('version', sa.INTEGER(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('contracts_tenant_id_fkey')),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], name=op.f('contracts_uploaded_by_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('contracts_pkey'))
    )
    
    # Create indexes for contracts table
    op.create_index(op.f('idx_contract_tenant_status'), 'contracts', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('idx_contract_created_at'), 'contracts', ['created_at'], unique=False)
    op.create_index(op.f('ix_contracts_tenant_id'), 'contracts', ['tenant_id'], unique=False)
    
    # Create clauses table
    op.create_table(
        'clauses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('contract_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('clause_number', sa.INTEGER(), nullable=False),
        sa.Column('clause_type', sa.VARCHAR(length=100), nullable=True),
        sa.Column('section_title', sa.VARCHAR(length=255), nullable=True),
        sa.Column('raw_text', sa.TEXT(), nullable=False),
        sa.Column('severity', postgresql.ENUM('critical', 'high', 'medium', 'low', 'info', name='clauseseverity', create_type=False), nullable=False, server_default='info'),
        sa.Column('risk_description', sa.TEXT(), nullable=True),
        sa.Column('legal_reasoning', sa.TEXT(), nullable=True),
        sa.Column('confidence_score', sa.INTEGER(), nullable=False),
        sa.Column('chromadb_id', sa.VARCHAR(length=255), nullable=True, unique=True),
        sa.Column('embedding_dimension', sa.INTEGER(), nullable=False, server_default='1536'),
        sa.Column('applicable_statute', sa.VARCHAR(length=255), nullable=True),
        sa.Column('statute_section', sa.VARCHAR(length=100), nullable=True),
        sa.Column('is_standard', sa.INTEGER(), nullable=False, server_default='1'),
        sa.Column('is_missing_mandatory', sa.INTEGER(), nullable=False, server_default='0'),
        sa.Column('is_jurisdiction_mismatch', sa.INTEGER(), nullable=False, server_default='0'),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('version', sa.INTEGER(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], name=op.f('clauses_contract_id_fkey')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('clauses_tenant_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('clauses_pkey'))
    )
    
    # Create indexes for clauses table
    op.create_index(op.f('idx_clause_contract_severity'), 'clauses', ['contract_id', 'severity'], unique=False)
    op.create_index(op.f('idx_clause_tenant_type'), 'clauses', ['tenant_id', 'clause_type'], unique=False)
    op.create_index(op.f('ix_clauses_contract_id'), 'clauses', ['contract_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove Contract and Clause tables."""
    # Drop clauses table and indexes
    op.drop_index(op.f('ix_clauses_contract_id'), table_name='clauses')
    op.drop_index(op.f('idx_clause_tenant_type'), table_name='clauses')
    op.drop_index(op.f('idx_clause_contract_severity'), table_name='clauses')
    op.drop_table('clauses')
    
    # Drop contracts table and indexes
    op.drop_index(op.f('ix_contracts_tenant_id'), table_name='contracts')
    op.drop_index(op.f('idx_contract_created_at'), table_name='contracts')
    op.drop_index(op.f('idx_contract_tenant_status'), table_name='contracts')
    op.drop_table('contracts')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS contractstatus')
    op.execute('DROP TYPE IF EXISTS clauseseverity')
