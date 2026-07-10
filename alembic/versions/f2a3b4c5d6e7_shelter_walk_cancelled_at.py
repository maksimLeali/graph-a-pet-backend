"""shelter_walk_cancelled_at

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-07-10

Adds cancelled_at to shelter_walks. Needed to tell whether a cancelled walk
was cancelled today (operational lists show it) vs on a previous day (only
history screens should, not implemented yet).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f2a3b4c5d6e7'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('shelter_walks', sa.Column('cancelled_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('shelter_walks', 'cancelled_at')
