"""added main colors to media

Revision ID: fa2e8943f745
Revises: 75a4ce9a3356
Create Date: 2023-05-02 15:14:00.142798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa2e8943f745'
down_revision = '75a4ce9a3356'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('medias', sa.Column('main_colors', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('medias', 'main_colors')
    # ### end Alembic commands ###
