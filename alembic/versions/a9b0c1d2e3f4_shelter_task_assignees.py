"""shelter_task_assignees

Revision ID: a9b0c1d2e3f4
Revises: f3c4d5e6f7a8
Create Date: 2026-07-09

Multi-assignee tasks: join table shelter_task_assignees replaces the single
shelter_tasks.assigned_to_id column. Existing assignments are migrated first,
then the old column is dropped.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a9b0c1d2e3f4'
down_revision = 'f3c4d5e6f7a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shelter_task_assignees',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['shelter_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id', 'user_id', name='ux_shelter_task_assignee'),
    )
    op.create_index('ix_shelter_task_assignees_task_id', 'shelter_task_assignees', ['task_id'], unique=False)
    op.create_index('ix_shelter_task_assignees_user_id', 'shelter_task_assignees', ['user_id'], unique=False)

    # migrate existing single assignments into the join table
    op.execute(
        "INSERT INTO shelter_task_assignees (id, created_at, task_id, user_id) "
        "SELECT id || ':' || assigned_to_id, created_at, id, assigned_to_id "
        "FROM shelter_tasks WHERE assigned_to_id IS NOT NULL"
    )

    op.drop_constraint('shelter_tasks_assigned_to_id_fkey', 'shelter_tasks', type_='foreignkey')
    op.drop_column('shelter_tasks', 'assigned_to_id')


def downgrade() -> None:
    op.add_column('shelter_tasks', sa.Column('assigned_to_id', sa.String(), nullable=True))
    op.create_foreign_key('shelter_tasks_assigned_to_id_fkey', 'shelter_tasks', 'users', ['assigned_to_id'], ['id'])
    # restore a single assignee (first by created_at) per task
    op.execute(
        "UPDATE shelter_tasks t SET assigned_to_id = a.user_id "
        "FROM ("
        "  SELECT DISTINCT ON (task_id) task_id, user_id FROM shelter_task_assignees "
        "  ORDER BY task_id, created_at"
        ") a WHERE a.task_id = t.id"
    )
    op.drop_index('ix_shelter_task_assignees_user_id', table_name='shelter_task_assignees')
    op.drop_index('ix_shelter_task_assignees_task_id', table_name='shelter_task_assignees')
    op.drop_table('shelter_task_assignees')
