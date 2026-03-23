"""Initial schema creation - Tenants, Roles, Users, AuditLogs

Revision ID: 001
Revises: 
Create Date: 2026-03-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema with Tenants, Roles, Users, and AuditLogs tables."""
    
    # Create ENUM type for subscription tier
    subscription_tier_enum = postgresql.ENUM(
        'free', 'pro', 'enterprise',
        name='subscriptiontier',
        create_type=False
    )
    subscription_tier_enum.create(op.get_bind(), checkfirst=True)
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False, default=uuid4),
        sa.Column('company_name', sa.String(255), nullable=False, index=True),
        sa.Column('industry', sa.String(100), nullable=False),
        sa.Column('subscription_tier', subscription_tier_enum, default='free'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), default=1, nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False, default=uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('role_name', sa.String(100), nullable=False),
        sa.Column('permission_matrix', postgresql.JSON(), default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), default=1, nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_tenant_role_name', 'roles', ['tenant_id', 'role_name'])
    op.create_index('ix_roles_tenant_id', 'roles', ['tenant_id'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False, default=uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name_encrypted', sa.Text(), nullable=False),
        sa.Column('email_encrypted', sa.Text(), nullable=False),
        sa.Column('email_hash', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Integer(), default=1, nullable=False),
        sa.Column('email_verified', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), default=1, nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_tenant_email_hash', 'users', ['tenant_id', 'email_hash'])
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False, default=uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_tenant_event_created', 'audit_logs', ['tenant_id', 'event_type', 'created_at'])
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])


def downgrade() -> None:
    """Drop all tables and remove enum type."""
    
    # Drop audit_logs first (has foreign keys to other tables)
    op.drop_index('ix_audit_logs_tenant_id', table_name='audit_logs')
    op.drop_index('idx_tenant_event_created', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    # Drop users table
    op.drop_index('ix_users_tenant_id', table_name='users')
    op.drop_index('idx_tenant_email_hash', table_name='users')
    op.drop_table('users')
    
    # Drop roles table
    op.drop_index('ix_roles_tenant_id', table_name='roles')
    op.drop_index('idx_tenant_role_name', table_name='roles')
    op.drop_table('roles')
    
    # Drop tenants table
    op.drop_table('tenants')
    
    # Drop ENUM type
    subscription_tier_enum = postgresql.ENUM(
        'free', 'pro', 'enterprise',
        name='subscriptiontier',
        create_type=False
    )
    subscription_tier_enum.drop(op.get_bind(), checkfirst=True)
