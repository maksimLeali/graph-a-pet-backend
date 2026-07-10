"""shelter_walk_ratings

Revision ID: a2b3c4d5e6f7
Revises: f2a3b4c5d6e7
Create Date: 2026-07-10

Reuses the existing walkratingtype enum (from walk_ratings) so shelter dog
walks can be rated with the same categories as personal-pet walks.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a2b3c4d5e6f7'
down_revision = 'f2a3b4c5d6e7'
branch_labels = None
depends_on = None

# create_type=False: walkratingtype already exists (created by d3f7fa62c886)
walk_rating_type = postgresql.ENUM(
    'OVERALL', 'LEASH_PULLING', 'BEHAVIOR', 'AGGRESSION', 'CALM',
    name='walkratingtype', create_type=False,
)


def upgrade() -> None:
    op.create_table(
        'shelter_walk_ratings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('walk_id', sa.String(), nullable=False),
        sa.Column('type', walk_rating_type, nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['walk_id'], ['shelter_walks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_walk_ratings_walk_id', 'shelter_walk_ratings', ['walk_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_walk_ratings_walk_id', table_name='shelter_walk_ratings')
    op.drop_table('shelter_walk_ratings')
