"""donations_prereq_columns

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-07-13

Two small additive columns the donation domain needs on existing tables,
kept separate from the big donations-tables migration:

  * shelter_pets.is_published — gates public storefront/donation visibility
    for a pet (a pet must be explicitly published, separate from just
    belonging to a public shelter).
  * shelters.timezone — IANA timezone name, used to compute the
    shelter-local calendar-month boundaries for pet donation limits.
    Defaults to 'UTC' for every existing shelter.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd6e7f8a9b0c1'
down_revision = 'c5d6e7f8a9b0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'shelter_pets',
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'shelters',
        sa.Column('timezone', sa.String(), nullable=False, server_default='UTC'),
    )


def downgrade() -> None:
    op.drop_column('shelters', 'timezone')
    op.drop_column('shelter_pets', 'is_published')
