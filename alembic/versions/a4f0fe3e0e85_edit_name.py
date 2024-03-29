"""edit name 

Revision ID: a4f0fe3e0e85
Revises: 9cbc11c99434
Create Date: 2022-11-28 12:04:39.965982

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4f0fe3e0e85'
down_revision = '9cbc11c99434'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('statistics', sa.Column('active_users', sa.Integer(), nullable=True))
    op.drop_column('statistics', 'active_per_day')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('statistics', sa.Column('active_per_day', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('statistics', 'active_users')
    # ### end Alembic commands ###
