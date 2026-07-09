"""shelter public profile fields

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-07-09

Adds opt-in public-discovery profile fields to shelters: description,
public contacts, volunteer application availability, and an approximate
public location. All nullable / defaulted so existing rows are unaffected;
discovery only surfaces PUBLIC + VERIFIED shelters regardless of these.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b6c7d8e9f0a1'
down_revision = 'a5b6c7d8e9f0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('shelters', sa.Column('public_description', sa.Text(), nullable=True))
    op.add_column('shelters', sa.Column('public_contact_email', sa.String(), nullable=True))
    op.add_column('shelters', sa.Column('public_contact_phone', sa.String(), nullable=True))
    op.add_column('shelters', sa.Column('accepts_volunteers', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('shelters', sa.Column('public_location_label', sa.String(), nullable=True))
    op.add_column('shelters', sa.Column('public_lat', sa.Float(), nullable=True))
    op.add_column('shelters', sa.Column('public_lng', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('shelters', 'public_lng')
    op.drop_column('shelters', 'public_lat')
    op.drop_column('shelters', 'public_location_label')
    op.drop_column('shelters', 'accepts_volunteers')
    op.drop_column('shelters', 'public_contact_phone')
    op.drop_column('shelters', 'public_contact_email')
    op.drop_column('shelters', 'public_description')
