"""donation_notifications

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8
Create Date: 2026-07-16

Adds the DONATION_RECEIVED notification type + DONATION entity type:
every shelter member with an account gets a notification when a donation
to the shelter (or to one of its pets) succeeds.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b9'
down_revision = 'b2c3d4e5f6a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'DONATION_RECEIVED'")
    op.execute("ALTER TYPE notificationentitytype ADD VALUE IF NOT EXISTS 'DONATION'")


def downgrade() -> None:
    # PostgreSQL cannot drop enum values; harmless to leave them in place
    pass
