"""shelter_ownership_transfers

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-07-09

Lets the current OWNER of a shelter/workspace hand off technical ownership to
another user, who must accept. Also extends the notification enums so the
destination user gets a real inbox notification.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f4a5b6c7d8e9'
down_revision = 'e3f4a5b6c7d8'
branch_labels = None
depends_on = None

# create_type=False so table DDL never auto-emits CREATE TYPE; created once below
transfer_status = postgresql.ENUM(
    'PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED', 'EXPIRED',
    name='shelterownershiptransferstatus', create_type=False,
)
# rolelevel already exists (created with shelter_roles); reuse without recreating
role_level = postgresql.ENUM(
    'OWNER', 'MANAGER', 'STAFF', 'VOLUNTEER', name='rolelevel', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    transfer_status.create(bind, checkfirst=True)

    op.create_table(
        'shelter_ownership_transfers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('from_user_id', sa.String(), nullable=False),
        sa.Column('to_user_id', sa.String(), nullable=False),
        sa.Column('new_role_for_previous_owner', role_level, nullable=True),
        sa.Column('status', transfer_status, nullable=False, server_default='PENDING'),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_ownership_transfers_shelter_id', 'shelter_ownership_transfers', ['shelter_id'], unique=False)
    op.create_index('ix_shelter_ownership_transfers_to_user_id', 'shelter_ownership_transfers', ['to_user_id'], unique=False)
    op.create_index('ix_shelter_ownership_transfers_status', 'shelter_ownership_transfers', ['status'], unique=False)

    # new notification kind for the destination user's inbox
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'SHELTER_OWNERSHIP_TRANSFER'")
    op.execute("ALTER TYPE notificationentitytype ADD VALUE IF NOT EXISTS 'SHELTER_OWNERSHIP_TRANSFER'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums; the added notification enum values
    # are left in place on downgrade (harmless, matches existing precedent
    # for additive enum changes in this codebase).
    op.drop_index('ix_shelter_ownership_transfers_status', table_name='shelter_ownership_transfers')
    op.drop_index('ix_shelter_ownership_transfers_to_user_id', table_name='shelter_ownership_transfers')
    op.drop_index('ix_shelter_ownership_transfers_shelter_id', table_name='shelter_ownership_transfers')
    op.drop_table('shelter_ownership_transfers')
    transfer_status.drop(op.get_bind(), checkfirst=True)
