"""movement_type_transfer_payout

Revision ID: 6e9c38c5156e
Revises: f8a9b0c1d2e3
Create Date: 2026-07-13

Adds TRANSFER and PAYOUT to the movementtype enum (the task's ledger
section lists 9 movement kinds; the first cut of the enum only had 8).
`ALTER TYPE ... ADD VALUE` cannot run inside the transaction Alembic
normally wraps a migration in, hence `autocommit_block()`.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '6e9c38c5156e'
down_revision = 'f8a9b0c1d2e3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE movementtype ADD VALUE IF NOT EXISTS 'TRANSFER'")
        op.execute("ALTER TYPE movementtype ADD VALUE IF NOT EXISTS 'PAYOUT'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums — downgrading this one is a
    # no-op; the extra labels are harmless if left in place.
    pass
