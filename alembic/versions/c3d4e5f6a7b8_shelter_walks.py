"""shelter_walks

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shelter_walks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_pet_id', sa.String(), nullable=False),
        sa.Column('walker_id', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='shelterwalkstatus'), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_pet_id'], ['shelter_pets.id'], ),
        sa.ForeignKeyConstraint(['walker_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_walks_shelter_pet_id', 'shelter_walks', ['shelter_pet_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_walks_shelter_pet_id', table_name='shelter_walks')
    op.drop_table('shelter_walks')
    sa.Enum(name='shelterwalkstatus').drop(op.get_bind(), checkfirst=True)
