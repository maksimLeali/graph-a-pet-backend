"""shelter_tasks.template_id (recurrence materialization)

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b8c9d0e1f2a3'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('shelter_tasks', sa.Column('template_id', sa.String(), nullable=True))
    op.create_foreign_key(
        'fk_shelter_tasks_template_id', 'shelter_tasks', 'shelter_tasks',
        ['template_id'], ['id'], ondelete='SET NULL',
    )
    op.create_index('ix_shelter_tasks_template_id', 'shelter_tasks', ['template_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_tasks_template_id', table_name='shelter_tasks')
    op.drop_constraint('fk_shelter_tasks_template_id', 'shelter_tasks', type_='foreignkey')
    op.drop_column('shelter_tasks', 'template_id')
