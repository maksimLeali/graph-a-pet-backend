"""rbac_core

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-07-12

Permission-first RBAC core: permissions, roles, role_permissions, user_roles,
shelter_memberships, authorization_audit_logs. Legacy shelter_roles is left
untouched; it keeps working during the shadow/backfill phases.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b4c5d6e7f8a9'
down_revision = 'a3b4c5d6e7f8'
branch_labels = None
depends_on = None

# create_type=False so table DDL never auto-emits CREATE TYPE; created once below
rbac_scope_type = postgresql.ENUM(
    'PLATFORM', 'SHELTER', name='rbacscopetype', create_type=False,
)
user_role_status = postgresql.ENUM(
    'ACTIVE', 'SUSPENDED', 'REVOKED', 'EXPIRED',
    name='userrolestatus', create_type=False,
)
membership_status = postgresql.ENUM(
    'INVITED', 'PENDING_ONBOARDING', 'ACTIVE', 'SUSPENDED', 'LEFT', 'REVOKED',
    name='sheltermembershipstatus', create_type=False,
)
membership_source = postgresql.ENUM(
    'INVITE', 'JOIN_REQUEST', 'CLAIM', 'OWNERSHIP_TRANSFER', 'MANUAL', 'WORKSPACE_CREATOR',
    name='sheltermembershipsource', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    rbac_scope_type.create(bind, checkfirst=True)
    user_role_status.create(bind, checkfirst=True)
    membership_status.create(bind, checkfirst=True)
    membership_source.create(bind, checkfirst=True)

    op.create_table(
        'permissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scope_type', rbac_scope_type, nullable=False),
        sa.Column('risk_level', sa.String(), nullable=False, server_default='LOW'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_permissions_key', 'permissions', ['key'], unique=True)

    op.create_table(
        'roles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scope_type', rbac_scope_type, nullable=False),
        sa.Column('owner_shelter_id', sa.String(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_assignable', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('grants_all_permissions', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_shelter_id'], ['shelters.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_roles_code', 'roles', ['code'], unique=True)
    op.create_index('ix_roles_owner_shelter_id', 'roles', ['owner_shelter_id'], unique=False)

    op.create_table(
        'role_permissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('role_id', sa.String(), nullable=False),
        sa.Column('permission_id', sa.String(), nullable=False),
        sa.Column('granted_by_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['granted_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permissions_role_permission'),
    )
    op.create_index('ix_role_permissions_role_id', 'role_permissions', ['role_id'], unique=False)
    op.create_index('ix_role_permissions_permission_id', 'role_permissions', ['permission_id'], unique=False)

    op.create_table(
        'user_roles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role_id', sa.String(), nullable=False),
        sa.Column('shelter_id', sa.String(), nullable=True),
        sa.Column('status', user_role_status, nullable=False, server_default='ACTIVE'),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('assigned_by_id', sa.String(), nullable=True),
        sa.Column('revoked_by_id', sa.String(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['revoked_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_roles_user_id', 'user_roles', ['user_id'], unique=False)
    op.create_index('ix_user_roles_role_id', 'user_roles', ['role_id'], unique=False)
    op.create_index('ix_user_roles_shelter_id', 'user_roles', ['shelter_id'], unique=False)
    op.create_index('ix_user_roles_status', 'user_roles', ['status'], unique=False)
    # UNIQUE(user_id, role_id, shelter_id) with NULL-safe handling:
    # PostgreSQL treats NULLs as distinct, so platform-scoped rows need their
    # own partial unique index.
    op.create_index(
        'uq_user_roles_user_role_shelter', 'user_roles',
        ['user_id', 'role_id', 'shelter_id'], unique=True,
        postgresql_where=sa.text('shelter_id IS NOT NULL'),
    )
    op.create_index(
        'uq_user_roles_user_role_platform', 'user_roles',
        ['user_id', 'role_id'], unique=True,
        postgresql_where=sa.text('shelter_id IS NULL'),
    )

    op.create_table(
        'shelter_memberships',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', membership_status, nullable=False, server_default='ACTIVE'),
        sa.Column('source', membership_source, nullable=False, server_default='MANUAL'),
        sa.Column('invited_by_id', sa.String(), nullable=True),
        sa.Column('approved_by_id', sa.String(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('suspended_at', sa.DateTime(), nullable=True),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shelter_id', 'user_id', name='uq_shelter_memberships_shelter_user'),
    )
    op.create_index('ix_shelter_memberships_shelter_id', 'shelter_memberships', ['shelter_id'], unique=False)
    op.create_index('ix_shelter_memberships_user_id', 'shelter_memberships', ['user_id'], unique=False)
    op.create_index('ix_shelter_memberships_status', 'shelter_memberships', ['status'], unique=False)

    op.create_table(
        'authorization_audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('actor_user_id', sa.String(), nullable=True),
        sa.Column('target_user_id', sa.String(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=True),
        sa.Column('role_id', sa.String(), nullable=True),
        sa.Column('permission_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('before_data', postgresql.JSONB(), nullable=True),
        sa.Column('after_data', postgresql.JSONB(), nullable=True),
        sa.Column('request_id', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_authorization_audit_logs_actor_user_id', 'authorization_audit_logs', ['actor_user_id'], unique=False)
    op.create_index('ix_authorization_audit_logs_shelter_id', 'authorization_audit_logs', ['shelter_id'], unique=False)
    op.create_index('ix_authorization_audit_logs_action', 'authorization_audit_logs', ['action'], unique=False)
    op.create_index('ix_authorization_audit_logs_created_at', 'authorization_audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_authorization_audit_logs_created_at', table_name='authorization_audit_logs')
    op.drop_index('ix_authorization_audit_logs_action', table_name='authorization_audit_logs')
    op.drop_index('ix_authorization_audit_logs_shelter_id', table_name='authorization_audit_logs')
    op.drop_index('ix_authorization_audit_logs_actor_user_id', table_name='authorization_audit_logs')
    op.drop_table('authorization_audit_logs')

    op.drop_index('ix_shelter_memberships_status', table_name='shelter_memberships')
    op.drop_index('ix_shelter_memberships_user_id', table_name='shelter_memberships')
    op.drop_index('ix_shelter_memberships_shelter_id', table_name='shelter_memberships')
    op.drop_table('shelter_memberships')

    op.drop_index('uq_user_roles_user_role_platform', table_name='user_roles')
    op.drop_index('uq_user_roles_user_role_shelter', table_name='user_roles')
    op.drop_index('ix_user_roles_status', table_name='user_roles')
    op.drop_index('ix_user_roles_shelter_id', table_name='user_roles')
    op.drop_index('ix_user_roles_role_id', table_name='user_roles')
    op.drop_index('ix_user_roles_user_id', table_name='user_roles')
    op.drop_table('user_roles')

    op.drop_index('ix_role_permissions_permission_id', table_name='role_permissions')
    op.drop_index('ix_role_permissions_role_id', table_name='role_permissions')
    op.drop_table('role_permissions')

    op.drop_index('ix_roles_owner_shelter_id', table_name='roles')
    op.drop_index('ix_roles_code', table_name='roles')
    op.drop_table('roles')

    op.drop_index('ix_permissions_key', table_name='permissions')
    op.drop_table('permissions')

    bind = op.get_bind()
    membership_source.drop(bind, checkfirst=True)
    membership_status.drop(bind, checkfirst=True)
    user_role_status.drop(bind, checkfirst=True)
    rbac_scope_type.drop(bind, checkfirst=True)
