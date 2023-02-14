"""added deleted_by

Revision ID: 39cbe8abeb10
Revises: 38e98d6ad9a0
Create Date: 2023-02-10 11:06:17.691456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39cbe8abeb10'
down_revision = '38e98d6ad9a0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('damnationes_memoriae', sa.Column('deleted_by', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('damnationes_memoriae', 'deleted_by')
    # ### end Alembic commands ###