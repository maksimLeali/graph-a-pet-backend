"""remove constraint

Revision ID: ff0efc88e709
Revises: 0365689ed169
Create Date: 2022-07-18 09:58:17.653303

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff0efc88e709'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('treatments_booster_id_fkey', 'treatments', type_='foreignkey')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('treatments_booster_id_fkey', 'treatments', 'treatments', ['booster_id'], ['id'])
    # ### end Alembic commands ###