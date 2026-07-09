"""shelter_claim_requests

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-07-09

Lets a user request official verification of a PERSONAL_WORKSPACE or an
UNVERIFIED OFFICIAL_SHELTER. An admin reviews the request; on approval the
shelter becomes a VERIFIED OFFICIAL_SHELTER and the requester is assigned as
OWNER.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a5b6c7d8e9f0'
down_revision = 'f4a5b6c7d8e9'
branch_labels = None
depends_on = None

# create_type=False so table DDL never auto-emits CREATE TYPE; created once below
claim_status = postgresql.ENUM(
    'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED',
    name='shelterclaimrequeststatus', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    claim_status.create(bind, checkfirst=True)

    op.create_table(
        'shelter_claim_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('requester_user_id', sa.String(), nullable=False),
        sa.Column('status', claim_status, nullable=False, server_default='PENDING'),
        sa.Column('proof_data', postgresql.JSONB(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('decision_note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['requester_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_claim_requests_shelter_id', 'shelter_claim_requests', ['shelter_id'], unique=False)
    op.create_index('ix_shelter_claim_requests_requester_user_id', 'shelter_claim_requests', ['requester_user_id'], unique=False)
    op.create_index('ix_shelter_claim_requests_status', 'shelter_claim_requests', ['status'], unique=False)

    # new notification kind for the requester's / adjusted-owner's inbox
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'SHELTER_CLAIM_REQUEST'")
    op.execute("ALTER TYPE notificationentitytype ADD VALUE IF NOT EXISTS 'SHELTER_CLAIM_REQUEST'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums; the added notification enum values
    # are left in place on downgrade (harmless, matches existing precedent
    # for additive enum changes in this codebase).
    op.drop_index('ix_shelter_claim_requests_status', table_name='shelter_claim_requests')
    op.drop_index('ix_shelter_claim_requests_requester_user_id', table_name='shelter_claim_requests')
    op.drop_index('ix_shelter_claim_requests_shelter_id', table_name='shelter_claim_requests')
    op.drop_table('shelter_claim_requests')
    claim_status.drop(op.get_bind(), checkfirst=True)
