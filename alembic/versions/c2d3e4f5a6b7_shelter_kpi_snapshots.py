"""shelter_kpi_snapshots: storicizzazione giornaliera KPI operativi

Una riga per shelter per giorno (unique shelter_id + snapshot_date),
popolata dal cron giornaliero.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c2d3e4f5a6b7'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None

_KPI = [
    'walks_completed_today', 'walks_planned_today', 'pets_needing_walk',
    'tasks_pending', 'tasks_overdue', 'tasks_completed_today',
    'boxes_total', 'boxes_free', 'boxes_occupied', 'boxes_full',
    'boxes_out_of_service', 'pets_total', 'pets_without_box', 'low_stock_count',
]


def upgrade() -> None:
    op.create_table(
        'shelter_kpi_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        *[sa.Column(k, sa.Integer(), nullable=True) for k in _KPI],
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shelter_id', 'snapshot_date', name='uq_shelter_kpi_day'),
    )
    op.create_index('ix_shelter_kpi_snapshots_shelter_id', 'shelter_kpi_snapshots', ['shelter_id'], unique=False)
    op.create_index('ix_shelter_kpi_snapshots_snapshot_date', 'shelter_kpi_snapshots', ['snapshot_date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_kpi_snapshots_snapshot_date', table_name='shelter_kpi_snapshots')
    op.drop_index('ix_shelter_kpi_snapshots_shelter_id', table_name='shelter_kpi_snapshots')
    op.drop_table('shelter_kpi_snapshots')
