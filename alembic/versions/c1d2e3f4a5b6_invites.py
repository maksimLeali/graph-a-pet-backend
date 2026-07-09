"""ownership status + shelter_invites

Revision ID: c1d2e3f4a5b6
Revises: b0c1d2e3f4a5
Create Date: 2026-07-09

Pet ownership becomes invitable (status PENDING/ACCEPTED/REJECTED) and a
minimal shelter_invites entity is added. Both feed the notification inbox.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'b0c1d2e3f4a5'
branch_labels = None
depends_on = None

# create_type=False so column/table DDL never auto-emits CREATE TYPE; the types
# are created once, explicitly, with checkfirst below.
ownership_status = postgresql.ENUM(
    'PENDING', 'ACCEPTED', 'REJECTED', name='ownershipstatus', create_type=False,
)
shelter_invite_status = postgresql.ENUM(
    'PENDING', 'ACCEPTED', 'REJECTED', name='shelterinvitestatus', create_type=False,
)
# rolelevel already exists (created with shelter_roles); reuse without recreating
role_level = postgresql.ENUM(
    'OWNER', 'MANAGER', 'STAFF', 'VOLUNTEER', name='rolelevel', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    ownership_status.create(bind, checkfirst=True)
    shelter_invite_status.create(bind, checkfirst=True)

    # existing ownerships are effective -> ACCEPTED
    op.add_column('ownerships', sa.Column(
        'status', ownership_status, nullable=False, server_default='ACCEPTED',
    ))

    op.create_table(
        'shelter_invites',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role', role_level, nullable=False),
        sa.Column('status', shelter_invite_status, nullable=False, server_default='PENDING'),
        sa.Column('invited_by_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_invites_shelter_id', 'shelter_invites', ['shelter_id'], unique=False)
    op.create_index('ix_shelter_invites_user_id', 'shelter_invites', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_invites_user_id', table_name='shelter_invites')
    op.drop_index('ix_shelter_invites_shelter_id', table_name='shelter_invites')
    op.drop_table('shelter_invites')
    op.drop_column('ownerships', 'status')
    shelter_invite_status.drop(op.get_bind(), checkfirst=True)
    ownership_status.drop(op.get_bind(), checkfirst=True)
