"""shelter_task_volunteer_assignee

Revision ID: e1f2a3b4c5d6
Revises: d8e9f0a1b2c3
Create Date: 2026-07-10

Lets a shelter_task be assigned to a shelter_person (contact/volunteer
without an app account) in addition to a User. user_id becomes nullable;
exactly one of user_id / shelter_person_id is set per assignee row,
enforced in the domain layer (matching the shelter_walks convention).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'd8e9f0a1b2c3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('shelter_task_assignees', 'user_id', existing_type=sa.String(), nullable=True)
    op.add_column('shelter_task_assignees', sa.Column('shelter_person_id', sa.String(), nullable=True))
    op.create_foreign_key(
        'fk_shelter_task_assignees_shelter_person_id', 'shelter_task_assignees',
        'shelter_people', ['shelter_person_id'], ['id'],
    )
    op.create_index(
        'ix_shelter_task_assignees_shelter_person_id', 'shelter_task_assignees',
        ['shelter_person_id'], unique=False,
    )
    op.create_unique_constraint(
        'ux_shelter_task_assignee_shelter_person', 'shelter_task_assignees',
        ['task_id', 'shelter_person_id'],
    )


def downgrade() -> None:
    op.drop_constraint('ux_shelter_task_assignee_shelter_person', 'shelter_task_assignees', type_='unique')
    op.drop_index('ix_shelter_task_assignees_shelter_person_id', table_name='shelter_task_assignees')
    op.drop_constraint('fk_shelter_task_assignees_shelter_person_id', 'shelter_task_assignees', type_='foreignkey')
    op.drop_column('shelter_task_assignees', 'shelter_person_id')
    op.alter_column('shelter_task_assignees', 'user_id', existing_type=sa.String(), nullable=False)
