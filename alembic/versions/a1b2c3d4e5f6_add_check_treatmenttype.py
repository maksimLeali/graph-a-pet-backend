"""add CHECK to treatmenttype enum

Revision ID: a1b2c3d4e5f6
Revises: d3f7fa62c886
Create Date: 2026-07-03

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd3f7fa62c886'
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE treatmenttype ADD VALUE IF NOT EXISTS 'CHECK' BEFORE 'CURE'"
        )


def downgrade():
    # Postgres cannot drop a single enum value; no-op.
    pass
