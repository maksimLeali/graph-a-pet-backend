"""shelter_walk_volunteer_walker

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-07-09

Lets a shelter_walk be assigned to a shelter_person (contact/volunteer
without an app account) instead of only a User. walker_id becomes nullable;
exactly one of walker_id / shelter_person_id is set, enforced in the
domain layer (not a DB constraint, matching existing conventions here).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd8e9f0a1b2c3'
down_revision = 'c7d8e9f0a1b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('shelter_walks', 'walker_id', existing_type=sa.String(), nullable=True)
    op.add_column('shelter_walks', sa.Column('shelter_person_id', sa.String(), nullable=True))
    op.create_foreign_key(
        'fk_shelter_walks_shelter_person_id', 'shelter_walks',
        'shelter_people', ['shelter_person_id'], ['id'],
    )
    op.create_index('ix_shelter_walks_shelter_person_id', 'shelter_walks', ['shelter_person_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_walks_shelter_person_id', table_name='shelter_walks')
    op.drop_constraint('fk_shelter_walks_shelter_person_id', 'shelter_walks', type_='foreignkey')
    op.drop_column('shelter_walks', 'shelter_person_id')
    op.alter_column('shelter_walks', 'walker_id', existing_type=sa.String(), nullable=False)
