"""shelter_ownerships

Revision ID: 4c512b45c3c4
Revises: a7c4e91b3d05
Create Date: 2026-07-17

Technical ownership of shelters, separated from RBAC authorization. Legacy
OWNER rows in shelter_roles stay untouched until the backfill copies them
here with source MIGRATION and the cutover verifies every shelter has at
least one ACTIVE owner.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4c512b45c3c4'
down_revision = 'a7c4e91b3d05'
branch_labels = None
depends_on = None

ownership_status = postgresql.ENUM(
    'ACTIVE', 'TRANSFER_PENDING', 'ENDED', 'REVOKED',
    name='shelterownershipstatus', create_type=False,
)
ownership_source = postgresql.ENUM(
    'WORKSPACE_CREATOR', 'CLAIM_APPROVAL', 'OWNERSHIP_TRANSFER',
    'PLATFORM_ASSIGNMENT', 'MIGRATION',
    name='shelterownershipsource', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    ownership_status.create(bind, checkfirst=True)
    ownership_source.create(bind, checkfirst=True)

    op.create_table(
        'shelter_ownerships',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', ownership_status, nullable=False),
        sa.Column('source', ownership_source, nullable=False),
        sa.Column('created_by_id', sa.String(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_ownerships_shelter_id', 'shelter_ownerships', ['shelter_id'])
    op.create_index('ix_shelter_ownerships_user_id', 'shelter_ownerships', ['user_id'])
    op.create_index('ix_shelter_ownerships_status', 'shelter_ownerships', ['status'])
    # one ACTIVE ownership per (shelter, user); historical rows are unconstrained
    op.create_index(
        'uq_shelter_ownerships_active_shelter_user',
        'shelter_ownerships',
        ['shelter_id', 'user_id'],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )


def downgrade() -> None:
    op.drop_index('uq_shelter_ownerships_active_shelter_user', table_name='shelter_ownerships')
    op.drop_index('ix_shelter_ownerships_status', table_name='shelter_ownerships')
    op.drop_index('ix_shelter_ownerships_user_id', table_name='shelter_ownerships')
    op.drop_index('ix_shelter_ownerships_shelter_id', table_name='shelter_ownerships')
    op.drop_table('shelter_ownerships')
    bind = op.get_bind()
    ownership_status.drop(bind, checkfirst=True)
    ownership_source.drop(bind, checkfirst=True)
