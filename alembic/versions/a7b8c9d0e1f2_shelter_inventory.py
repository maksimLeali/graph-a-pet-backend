"""shelter_inventory items + movements

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shelter_inventory_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=160), nullable=False),
        sa.Column('category', sa.Enum('FOOD_DRY', 'FOOD_WET', 'MEDICINE', 'HYGIENE', 'EQUIPMENT', 'OTHER', name='inventorycategory'), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('minimum_threshold', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_inventory_items_shelter_id', 'shelter_inventory_items', ['shelter_id'], unique=False)

    op.create_table(
        'shelter_inventory_movements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('movement_type', sa.Enum('RESTOCK', 'CONSUMPTION', 'DONATION', 'WASTE', 'ADJUSTMENT', name='movementtype'), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('registered_by_id', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['shelter_inventory_items.id'], ),
        sa.ForeignKeyConstraint(['registered_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_inventory_movements_item_id', 'shelter_inventory_movements', ['item_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_inventory_movements_item_id', table_name='shelter_inventory_movements')
    op.drop_table('shelter_inventory_movements')
    op.drop_index('ix_shelter_inventory_items_shelter_id', table_name='shelter_inventory_items')
    op.drop_table('shelter_inventory_items')
    sa.Enum(name='movementtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='inventorycategory').drop(op.get_bind(), checkfirst=True)
