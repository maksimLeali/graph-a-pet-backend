"""funding_need_goals

Revision ID: a7c4e91b3d05
Revises: d4e5f6a7b8c0
Create Date: 2026-07-16

Turns pet funding needs into monthly goals ("traguardi"): adds a
shelter-managed urgency, a monthly-recurrence flag (the daily cron zeroes
collected_amount_cents on the 1st for recurring ACTIVE needs — see
schedules/donations.py) and the timestamp of the last reset.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a7c4e91b3d05'
down_revision = 'd4e5f6a7b8c0'
branch_labels = None
depends_on = None

funding_need_urgency = postgresql.ENUM(
    'NORMAL', 'URGENT', name='fundingneedurgency', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    funding_need_urgency.create(bind, checkfirst=True)

    op.add_column('pet_funding_needs', sa.Column(
        'urgency', funding_need_urgency, nullable=False, server_default='NORMAL',
    ))
    op.add_column('pet_funding_needs', sa.Column(
        'is_recurring_monthly', sa.Boolean(), nullable=False, server_default=sa.text('true'),
    ))
    op.add_column('pet_funding_needs', sa.Column('last_reset_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('pet_funding_needs', 'last_reset_at')
    op.drop_column('pet_funding_needs', 'is_recurring_monthly')
    op.drop_column('pet_funding_needs', 'urgency')
    funding_need_urgency.drop(op.get_bind(), checkfirst=True)
