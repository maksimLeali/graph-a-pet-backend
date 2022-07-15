"""first-try

Revision ID: ec63a7a5d0ba
Revises: 
Create Date: 2022-07-15 09:08:55.654695

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec63a7a5d0ba'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('treatments', sa.Column('name', sa.String))


def downgrade() -> None:
    op.drop_column('treatments', 'name')
