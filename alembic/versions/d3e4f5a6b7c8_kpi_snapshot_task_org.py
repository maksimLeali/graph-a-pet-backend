"""shelter_kpi_snapshots: KPI organizzazione task

Aggiunge tasks_total, tasks_recurring, tasks_due_this_week allo snapshot giornaliero.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd3e4f5a6b7c8'
down_revision = 'c2d3e4f5a6b7'
branch_labels = None
depends_on = None

_NEW = ['tasks_total', 'tasks_recurring', 'tasks_due_this_week']


def upgrade() -> None:
    for c in _NEW:
        op.add_column('shelter_kpi_snapshots', sa.Column(c, sa.Integer(), nullable=True))


def downgrade() -> None:
    for c in reversed(_NEW):
        op.drop_column('shelter_kpi_snapshots', c)
