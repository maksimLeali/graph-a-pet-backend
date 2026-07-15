"""shelter_default_pet_limit

Revision ID: 486d69ff1e7c
Revises: 6e9c38c5156e
Create Date: 2026-07-14

Adds a per-shelter default monthly donation limit for pets, overriding the
global platform default (stripe.default_pet_monthly_limit_cents) but still
overridable per-pet via PetDonationPolicy.custom_monthly_limit_cents. Lives
on stripe_connected_accounts (already the one-row-per-shelter home for
donation settings, e.g. donations_enabled) rather than a new table.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '486d69ff1e7c'
down_revision = '6e9c38c5156e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'stripe_connected_accounts',
        sa.Column('default_pet_monthly_limit_cents', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('stripe_connected_accounts', 'default_pet_monthly_limit_cents')
