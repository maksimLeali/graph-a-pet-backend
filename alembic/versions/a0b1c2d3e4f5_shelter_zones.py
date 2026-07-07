"""shelter_zones + zone_id NOT NULL su shelter_areas e shelter_boxes

Nuovo livello gerarchico Map -> Zone -> Area -> Box.
Backfill: una "Zona predefinita" per ogni mappa che ha già aree o box,
a cui vengono riassegnati aree e box esistenti prima di imporre NOT NULL.

Revision ID: a0b1c2d3e4f5
Revises: 58387be24d4b
Create Date: 2026-07-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a0b1c2d3e4f5'
down_revision = '58387be24d4b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- 1. tabella shelter_zones ---
    op.create_table(
        'shelter_zones',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('map_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.Column('x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('y', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('width', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('height', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['map_id'], ['shelter_maps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_zones_map_id', 'shelter_zones', ['map_id'], unique=False)

    # --- 2. colonne zone_id (nullable, per backfill) ---
    op.add_column('shelter_areas', sa.Column('zone_id', sa.String(), nullable=True))
    op.add_column('shelter_boxes', sa.Column('zone_id', sa.String(), nullable=True))

    # --- 3. backfill: una zona predefinita per ogni mappa con aree o box ---
    op.execute("""
        INSERT INTO shelter_zones (id, created_at, map_id, name, x, y, width, height, color)
        SELECT gen_random_uuid()::text, now(), m.id, 'Zona predefinita',
               0, 0, COALESCE(m.width, 0), COALESCE(m.height, 0), NULL
        FROM shelter_maps m
        WHERE EXISTS (SELECT 1 FROM shelter_areas a WHERE a.map_id = m.id)
           OR EXISTS (SELECT 1 FROM shelter_boxes b WHERE b.map_id = m.id)
    """)
    op.execute("""
        UPDATE shelter_areas a
        SET zone_id = z.id
        FROM shelter_zones z
        WHERE z.map_id = a.map_id AND a.zone_id IS NULL
    """)
    op.execute("""
        UPDATE shelter_boxes b
        SET zone_id = z.id
        FROM shelter_zones z
        WHERE z.map_id = b.map_id AND b.zone_id IS NULL
    """)

    # --- 4. NOT NULL + FK + index ---
    op.alter_column('shelter_areas', 'zone_id', existing_type=sa.String(), nullable=False)
    op.alter_column('shelter_boxes', 'zone_id', existing_type=sa.String(), nullable=False)
    op.create_index('ix_shelter_areas_zone_id', 'shelter_areas', ['zone_id'], unique=False)
    op.create_index('ix_shelter_boxes_zone_id', 'shelter_boxes', ['zone_id'], unique=False)
    op.create_foreign_key(
        'fk_shelter_areas_zone_id', 'shelter_areas', 'shelter_zones',
        ['zone_id'], ['id'], ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_shelter_boxes_zone_id', 'shelter_boxes', 'shelter_zones',
        ['zone_id'], ['id'], ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_shelter_boxes_zone_id', 'shelter_boxes', type_='foreignkey')
    op.drop_constraint('fk_shelter_areas_zone_id', 'shelter_areas', type_='foreignkey')
    op.drop_index('ix_shelter_boxes_zone_id', table_name='shelter_boxes')
    op.drop_index('ix_shelter_areas_zone_id', table_name='shelter_areas')
    op.drop_column('shelter_boxes', 'zone_id')
    op.drop_column('shelter_areas', 'zone_id')
    op.drop_index('ix_shelter_zones_map_id', table_name='shelter_zones')
    op.drop_table('shelter_zones')
