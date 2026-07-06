"""shelter_map_elements

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c9d0e1f2a3b4'
down_revision = 'b8c9d0e1f2a3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shelter_map_elements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('map_id', sa.String(), nullable=False),
        sa.Column('element_type', sa.Enum('WALL', 'DOOR', 'GATE', 'WATER_POINT', 'FEEDING_POINT', 'BENCH', 'TREE', 'OTHER', name='mapelementtype'), nullable=False),
        sa.Column('x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('y', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('width', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('height', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('rotation', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('label', sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(['map_id'], ['shelter_maps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_map_elements_map_id', 'shelter_map_elements', ['map_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_map_elements_map_id', table_name='shelter_map_elements')
    op.drop_table('shelter_map_elements')
    sa.Enum(name='mapelementtype').drop(op.get_bind(), checkfirst=True)
