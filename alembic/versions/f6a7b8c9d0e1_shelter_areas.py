"""shelter_areas + box.area_id FK

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shelter_areas',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('map_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.Column('area_type', sa.Enum('KENNEL', 'QUARANTINE', 'PLAYGROUND', 'MEDICAL', 'STORAGE', 'OFFICE', 'COMMON', 'OUTDOOR', 'OTHER', name='areatype'), nullable=True),
        sa.Column('x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('y', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('width', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('height', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['map_id'], ['shelter_maps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_areas_map_id', 'shelter_areas', ['map_id'], unique=False)
    # FK differita: shelter_boxes.area_id -> shelter_areas.id (colonna già esistente dalla fase 3)
    op.create_foreign_key(
        'fk_shelter_boxes_area_id', 'shelter_boxes', 'shelter_areas',
        ['area_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_shelter_boxes_area_id', 'shelter_boxes', type_='foreignkey')
    op.drop_index('ix_shelter_areas_map_id', table_name='shelter_areas')
    op.drop_table('shelter_areas')
    sa.Enum(name='areatype').drop(op.get_bind(), checkfirst=True)
