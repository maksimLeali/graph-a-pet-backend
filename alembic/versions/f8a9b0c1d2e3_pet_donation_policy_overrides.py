"""pet_donation_policy_overrides

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-07-13

Adds temporary-override fields to pet_donation_policies (amount, reason,
effective/expiry window) — split out from donations_core since it was
added right after that migration ran.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f8a9b0c1d2e3'
down_revision = 'e7f8a9b0c1d2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('pet_donation_policies', sa.Column('temporary_override_cents', sa.Integer(), nullable=True))
    op.add_column('pet_donation_policies', sa.Column('temporary_override_reason', sa.Text(), nullable=True))
    op.add_column('pet_donation_policies', sa.Column('temporary_override_effective_at', sa.DateTime(), nullable=True))
    op.add_column('pet_donation_policies', sa.Column('temporary_override_expires_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('pet_donation_policies', 'temporary_override_expires_at')
    op.drop_column('pet_donation_policies', 'temporary_override_effective_at')
    op.drop_column('pet_donation_policies', 'temporary_override_reason')
    op.drop_column('pet_donation_policies', 'temporary_override_cents')
