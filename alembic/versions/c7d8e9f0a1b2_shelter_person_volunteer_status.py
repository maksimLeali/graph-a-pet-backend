"""shelter_person_volunteer_status

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-07-09

Adds VOLUNTEER as a selectable status for shelter_people (contacts), so a
person can be classified as a volunteer instead of a plain visitor when
added to a shelter.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c7d8e9f0a1b2'
down_revision = 'b6c7d8e9f0a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE shelterpersonstatus ADD VALUE IF NOT EXISTS 'VOLUNTEER'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums; left in place on downgrade,
    # matching existing precedent for additive enum changes in this codebase.
    pass
