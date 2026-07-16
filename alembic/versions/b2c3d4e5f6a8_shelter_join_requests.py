"""shelter_join_requests

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-07-16

Volunteer application flow: a user applies to a shelter from its public
page; OWNER/MANAGER members get a SHELTER_JOIN_REQUEST notification and
approve or reject. Approval creates the VOLUNTEER ShelterRole.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a8'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None

# create_type=False so table DDL never auto-emits CREATE TYPE; created once below
join_status = postgresql.ENUM(
    'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED',
    name='shelterjoinrequeststatus', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    join_status.create(bind, checkfirst=True)

    op.create_table(
        'shelter_join_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', join_status, nullable=False, server_default='PENDING'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_join_requests_shelter_id', 'shelter_join_requests', ['shelter_id'], unique=False)
    op.create_index('ix_shelter_join_requests_user_id', 'shelter_join_requests', ['user_id'], unique=False)
    op.create_index('ix_shelter_join_requests_status', 'shelter_join_requests', ['status'], unique=False)

    # notification enum values already exist in models; make sure DB has them
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'SHELTER_JOIN_REQUEST'")
    op.execute("ALTER TYPE notificationentitytype ADD VALUE IF NOT EXISTS 'SHELTER_JOIN_REQUEST'")


def downgrade() -> None:
    op.drop_index('ix_shelter_join_requests_status', table_name='shelter_join_requests')
    op.drop_index('ix_shelter_join_requests_user_id', table_name='shelter_join_requests')
    op.drop_index('ix_shelter_join_requests_shelter_id', table_name='shelter_join_requests')
    op.drop_table('shelter_join_requests')
    postgresql.ENUM(name='shelterjoinrequeststatus').drop(op.get_bind(), checkfirst=True)
