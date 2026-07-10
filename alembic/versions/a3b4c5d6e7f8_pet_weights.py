"""pet_weights

Revision ID: a3b4c5d6e7f8
Revises: a2b3c4d5e6f7
Create Date: 2026-07-10

Weight history per pet (personal or shelter dog — both are `pets` rows),
decoupled from the single pets.weight_kg snapshot so it can be charted over
time. create_pet_weight keeps pets.weight_kg in sync with the latest entry.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a3b4c5d6e7f8'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'pet_weights',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('pet_id', sa.String(), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pet_weights_pet_id', 'pet_weights', ['pet_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_pet_weights_pet_id', table_name='pet_weights')
    op.drop_table('pet_weights')
