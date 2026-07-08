"""shelter_pets: transfer membership state

Adds is_active + left_at so a shelter transfer deactivates the source
membership instead of mutating it in place (one active ShelterPet per pet).

Revision ID: f3c4d5e6f7a8
Revises: f2b3c4d5e6f7
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f3c4d5e6f7a8'
down_revision = 'f2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'shelter_pets',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column('shelter_pets', sa.Column('left_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('shelter_pets', 'left_at')
    op.drop_column('shelter_pets', 'is_active')
