"""shelter_pet_assignments

Revision ID: d4e5f6a7b8c0
Revises: c3d4e5f6a7b9
Create Date: 2026-07-16

Links shelter members to shelter pets: the assigned member becomes the
default walker suggestion when planning a walk, and volunteers only see
pets/walks/tasks tied to them. Exactly one of user_id / shelter_person_id
is set per row (domain-enforced), mirroring shelter_task_assignees.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c0'
down_revision = 'c3d4e5f6a7b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shelter_pet_assignments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_pet_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('shelter_person_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_pet_id'], ['shelter_pets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shelter_person_id'], ['shelter_people.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shelter_pet_id', 'user_id',
                            name='ux_shelter_pet_assignment_user'),
        sa.UniqueConstraint('shelter_pet_id', 'shelter_person_id',
                            name='ux_shelter_pet_assignment_shelter_person'),
    )
    op.create_index('ix_shelter_pet_assignments_shelter_pet_id',
                    'shelter_pet_assignments', ['shelter_pet_id'], unique=False)
    op.create_index('ix_shelter_pet_assignments_user_id',
                    'shelter_pet_assignments', ['user_id'], unique=False)
    op.create_index('ix_shelter_pet_assignments_shelter_person_id',
                    'shelter_pet_assignments', ['shelter_person_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_pet_assignments_shelter_person_id', table_name='shelter_pet_assignments')
    op.drop_index('ix_shelter_pet_assignments_user_id', table_name='shelter_pet_assignments')
    op.drop_index('ix_shelter_pet_assignments_shelter_pet_id', table_name='shelter_pet_assignments')
    op.drop_table('shelter_pet_assignments')
