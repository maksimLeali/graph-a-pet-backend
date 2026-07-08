"""shelter_inventory_items: archive flow

Adds is_active, archived_at, archived_by_id so items with movement history are
archived instead of hard-deleted (the ledger must stay intact).

Revision ID: f2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f2b3c4d5e6f7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'shelter_inventory_items',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column('shelter_inventory_items', sa.Column('archived_at', sa.DateTime(), nullable=True))
    op.add_column('shelter_inventory_items', sa.Column('archived_by_id', sa.String(), nullable=True))
    op.create_foreign_key(
        'fk_shelter_inventory_items_archived_by_id_users',
        'shelter_inventory_items', 'users', ['archived_by_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_shelter_inventory_items_archived_by_id_users',
        'shelter_inventory_items', type_='foreignkey',
    )
    op.drop_column('shelter_inventory_items', 'archived_by_id')
    op.drop_column('shelter_inventory_items', 'archived_at')
    op.drop_column('shelter_inventory_items', 'is_active')
