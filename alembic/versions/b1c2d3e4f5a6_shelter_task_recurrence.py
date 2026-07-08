"""shelter_tasks: ricorrenza strutturata

Sostituisce la colonna stringa `recurrence_rule` con colonne strutturate
(freq/interval/weekdays/week_ordinal/time/start) così l'app costruisce la
ricorrenza da form senza scrivere JSON/stringhe a mano.

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = 'a0b1c2d3e4f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('shelter_tasks', sa.Column('recurrence_freq', sa.String(length=10), nullable=True))
    op.add_column('shelter_tasks', sa.Column('recurrence_interval', sa.Integer(), nullable=True))
    op.add_column('shelter_tasks', sa.Column('recurrence_weekdays', sa.ARRAY(sa.String()), nullable=True))
    op.add_column('shelter_tasks', sa.Column('recurrence_week_ordinal', sa.Integer(), nullable=True))
    op.add_column('shelter_tasks', sa.Column('recurrence_time', sa.String(length=5), nullable=True))
    op.add_column('shelter_tasks', sa.Column('recurrence_start', sa.DateTime(), nullable=True))
    op.drop_column('shelter_tasks', 'recurrence_rule')


def downgrade() -> None:
    op.add_column('shelter_tasks', sa.Column('recurrence_rule', sa.String(length=120), nullable=True))
    op.drop_column('shelter_tasks', 'recurrence_start')
    op.drop_column('shelter_tasks', 'recurrence_time')
    op.drop_column('shelter_tasks', 'recurrence_week_ordinal')
    op.drop_column('shelter_tasks', 'recurrence_weekdays')
    op.drop_column('shelter_tasks', 'recurrence_interval')
    op.drop_column('shelter_tasks', 'recurrence_freq')
