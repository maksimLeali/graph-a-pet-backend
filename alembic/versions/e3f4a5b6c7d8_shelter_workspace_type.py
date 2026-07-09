"""shelter type/verification/visibility

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-07-09

Lets normal users create private PERSONAL_WORKSPACE shelters alongside real
OFFICIAL_SHELTER rows. Existing shelters default to OFFICIAL_SHELTER /
VERIFIED / PUBLIC so their current (pre-feature) behavior is unchanged.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e3f4a5b6c7d8'
down_revision = 'd2e3f4a5b6c7'
branch_labels = None
depends_on = None

# create_type=False so column DDL never auto-emits CREATE TYPE; created once below
shelter_type = postgresql.ENUM(
    'OFFICIAL_SHELTER', 'PERSONAL_WORKSPACE', name='sheltertype', create_type=False,
)
shelter_verification_status = postgresql.ENUM(
    'UNVERIFIED', 'PENDING_CLAIM', 'VERIFIED', 'REJECTED',
    name='shelterverificationstatus', create_type=False,
)
shelter_visibility = postgresql.ENUM(
    'PRIVATE', 'UNLISTED', 'PUBLIC', name='sheltervisibility', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    shelter_type.create(bind, checkfirst=True)
    shelter_verification_status.create(bind, checkfirst=True)
    shelter_visibility.create(bind, checkfirst=True)

    op.add_column('shelters', sa.Column(
        'type', shelter_type, nullable=False, server_default='OFFICIAL_SHELTER',
    ))
    op.add_column('shelters', sa.Column(
        'verification_status', shelter_verification_status, nullable=False,
        server_default='VERIFIED',
    ))
    op.add_column('shelters', sa.Column(
        'visibility', shelter_visibility, nullable=False, server_default='PUBLIC',
    ))


def downgrade() -> None:
    op.drop_column('shelters', 'visibility')
    op.drop_column('shelters', 'verification_status')
    op.drop_column('shelters', 'type')
    shelter_visibility.drop(op.get_bind(), checkfirst=True)
    shelter_verification_status.drop(op.get_bind(), checkfirst=True)
    shelter_type.drop(op.get_bind(), checkfirst=True)
