"""shelter_tasks

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shelter_tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('shelter_pet_id', sa.String(), nullable=True),
        sa.Column('shelter_box_id', sa.String(), nullable=True),
        sa.Column('task_type', sa.Enum('CLEANING', 'DEEP_CLEANING', 'FEEDING', 'MEDICATION', 'GROOMING', 'OTHER', name='sheltertasktype'), nullable=False),
        sa.Column('area', sa.String(length=120), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED', name='taskstatus'), nullable=True),
        sa.Column('assigned_to_id', sa.String(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_by_id', sa.String(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('recurrence_rule', sa.String(length=120), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['shelter_pet_id'], ['shelter_pets.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['completed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_tasks_shelter_id', 'shelter_tasks', ['shelter_id'], unique=False)
    op.create_index('ix_shelter_tasks_shelter_pet_id', 'shelter_tasks', ['shelter_pet_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_tasks_shelter_pet_id', table_name='shelter_tasks')
    op.drop_index('ix_shelter_tasks_shelter_id', table_name='shelter_tasks')
    op.drop_table('shelter_tasks')
    sa.Enum(name='sheltertasktype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskstatus').drop(op.get_bind(), checkfirst=True)
