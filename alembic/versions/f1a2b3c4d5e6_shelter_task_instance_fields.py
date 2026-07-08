"""shelter_tasks: instance fields + cron idempotency

Adds scheduled_date, skipped_at, skipped_by_id and a unique constraint
(template_id, scheduled_date) so the daily cron cannot materialize the same
recurring instance twice.

Revision ID: f1a2b3c4d5e6
Revises: d3e4f5a6b7c8
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'd3e4f5a6b7c8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('shelter_tasks', sa.Column('scheduled_date', sa.Date(), nullable=True))
    op.add_column('shelter_tasks', sa.Column('skipped_at', sa.DateTime(), nullable=True))
    op.add_column('shelter_tasks', sa.Column('skipped_by_id', sa.String(), nullable=True))
    op.create_index('ix_shelter_tasks_scheduled_date', 'shelter_tasks', ['scheduled_date'])
    op.create_foreign_key(
        'fk_shelter_tasks_skipped_by_id_users', 'shelter_tasks', 'users',
        ['skipped_by_id'], ['id'],
    )
    # Backfill scheduled_date from scheduled_at for existing instances so the
    # unique constraint below can be created without violations.
    op.execute(
        "UPDATE shelter_tasks SET scheduled_date = CAST(scheduled_at AS date) "
        "WHERE scheduled_date IS NULL AND scheduled_at IS NOT NULL"
    )
    op.create_unique_constraint(
        'ux_shelter_task_template_scheduled_date', 'shelter_tasks',
        ['template_id', 'scheduled_date'],
    )


def downgrade() -> None:
    op.drop_constraint('ux_shelter_task_template_scheduled_date', 'shelter_tasks', type_='unique')
    op.drop_constraint('fk_shelter_tasks_skipped_by_id_users', 'shelter_tasks', type_='foreignkey')
    op.drop_index('ix_shelter_tasks_scheduled_date', table_name='shelter_tasks')
    op.drop_column('shelter_tasks', 'skipped_by_id')
    op.drop_column('shelter_tasks', 'skipped_at')
    op.drop_column('shelter_tasks', 'scheduled_date')
