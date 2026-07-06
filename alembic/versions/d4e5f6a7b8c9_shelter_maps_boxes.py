"""shelter_maps + shelter_boxes

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shelter_maps',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.Column('width', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('height', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('unit', sa.Enum('METERS', 'PIXELS', name='mapunit'), nullable=True),
        sa.Column('background_media_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['background_media_id'], ['medias.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_maps_shelter_id', 'shelter_maps', ['shelter_id'], unique=False)

    op.create_table(
        'shelter_boxes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('map_id', sa.String(), nullable=False),
        sa.Column('area_id', sa.String(), nullable=True),
        sa.Column('label', sa.String(length=60), nullable=False),
        sa.Column('x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('y', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('width', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('height', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('rotation', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('is_out_of_service', sa.Boolean(), nullable=True),
        sa.Column('last_cleaned_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['map_id'], ['shelter_maps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('map_id', 'label', name='ux_shelter_box_map_label'),
        sa.CheckConstraint('capacity > 0', name='ck_shelter_box_capacity_positive'),
    )
    op.create_index('ix_shelter_boxes_map_id', 'shelter_boxes', ['map_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_boxes_map_id', table_name='shelter_boxes')
    op.drop_table('shelter_boxes')
    op.drop_index('ix_shelter_maps_shelter_id', table_name='shelter_maps')
    op.drop_table('shelter_maps')
    sa.Enum(name='mapunit').drop(op.get_bind(), checkfirst=True)
