"""shelter_people

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-07-09

People known by a shelter that may not have an app account. Never creates User
rows; user_id is an optional link. Archived instead of hard-deleted.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd2e3f4a5b6c7'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None

# create_type=False so table DDL never auto-emits CREATE TYPE; created once below
person_status = postgresql.ENUM(
    'VISITOR', 'PENDING_INVITE', 'ACTIVE_USER', 'ARCHIVED',
    name='shelterpersonstatus', create_type=False,
)
person_source = postgresql.ENUM(
    'MANUAL', 'INVITE', 'VISIT', 'VOLUNTEER_REQUEST', 'IMPORT',
    name='shelterpersonsource', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    person_status.create(bind, checkfirst=True)
    person_source.create(bind, checkfirst=True)

    op.create_table(
        'shelter_people',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('status', person_status, nullable=False, server_default='VISITOR'),
        sa.Column('source', person_source, nullable=False, server_default='MANUAL'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.String(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('archived_by_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['archived_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_people_shelter_id', 'shelter_people', ['shelter_id'], unique=False)
    op.create_index('ix_shelter_people_user_id', 'shelter_people', ['user_id'], unique=False)
    op.create_index('ix_shelter_people_status', 'shelter_people', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_shelter_people_status', table_name='shelter_people')
    op.drop_index('ix_shelter_people_user_id', table_name='shelter_people')
    op.drop_index('ix_shelter_people_shelter_id', table_name='shelter_people')
    op.drop_table('shelter_people')
    person_source.drop(op.get_bind(), checkfirst=True)
    person_status.drop(op.get_bind(), checkfirst=True)
