"""shelter_box_occupancies

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shelter_box_occupancies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('box_id', sa.String(), nullable=False),
        sa.Column('shelter_pet_id', sa.String(), nullable=False),
        sa.Column('entered_at', sa.DateTime(), nullable=False),
        sa.Column('exited_at', sa.DateTime(), nullable=True),
        sa.Column('moved_by_id', sa.String(), nullable=True),
        sa.Column('reason', sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(['box_id'], ['shelter_boxes.id'], ),
        sa.ForeignKeyConstraint(['shelter_pet_id'], ['shelter_pets.id'], ),
        sa.ForeignKeyConstraint(['moved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('exited_at IS NULL OR exited_at >= entered_at', name='ck_occupancy_exit_after_enter'),
    )
    op.create_index('ix_shelter_box_occupancies_box_id', 'shelter_box_occupancies', ['box_id'], unique=False)
    op.create_index('ix_shelter_box_occupancies_shelter_pet_id', 'shelter_box_occupancies', ['shelter_pet_id'], unique=False)
    # al massimo una occupancy attiva per pet
    op.create_index(
        'ux_shelter_pet_active_occupancy',
        'shelter_box_occupancies',
        ['shelter_pet_id'],
        unique=True,
        postgresql_where=sa.text('exited_at IS NULL'),
    )


def downgrade() -> None:
    op.drop_index('ux_shelter_pet_active_occupancy', table_name='shelter_box_occupancies')
    op.drop_index('ix_shelter_box_occupancies_shelter_pet_id', table_name='shelter_box_occupancies')
    op.drop_index('ix_shelter_box_occupancies_box_id', table_name='shelter_box_occupancies')
    op.drop_table('shelter_box_occupancies')
