"""notifications

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-07-09

Internal notification inbox. Notifications are never the source of truth: each
row points to the real entity through entity_type/entity_id and the
pet_id/shelter_id/actor_user_id pointers. dedupe_key keeps cron idempotent.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b0c1d2e3f4a5'
down_revision = 'a9b0c1d2e3f4'
branch_labels = None
depends_on = None

notification_type = sa.Enum(
    'TREATMENT_REMINDER', 'PET_OWNERSHIP_INVITE', 'SHELTER_INVITE',
    'SHELTER_TASK_INSTANCE', 'SHELTER_JOIN_REQUEST', 'PET_BIRTHDAY',
    name='notificationtype',
)
notification_status = sa.Enum(
    'UNREAD', 'READ', 'DISMISSED', 'EXPIRED', name='notificationstatus',
)
notification_priority = sa.Enum(
    'LOW', 'NORMAL', 'HIGH', 'URGENT', name='notificationpriority',
)
notification_entity_type = sa.Enum(
    'PET', 'TREATMENT', 'OWNERSHIP', 'SHELTER', 'SHELTER_INVITE',
    'SHELTER_TASK', 'SHELTER_JOIN_REQUEST', name='notificationentitytype',
)


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('type', notification_type, nullable=False),
        sa.Column('status', notification_status, nullable=False),
        sa.Column('priority', notification_priority, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('entity_type', notification_entity_type, nullable=True),
        sa.Column('entity_id', sa.String(), nullable=True),
        sa.Column('action_url', sa.String(), nullable=True),
        sa.Column('actor_user_id', sa.String(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=True),
        sa.Column('pet_id', sa.String(), nullable=True),
        sa.Column('payload', postgresql.JSONB(), nullable=True),
        sa.Column('dedupe_key', sa.String(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dedupe_key', name='ux_notifications_dedupe_key'),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('ix_notifications_status', 'notifications', ['status'], unique=False)
    op.create_index('ix_notifications_dedupe_key', 'notifications', ['dedupe_key'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_notifications_dedupe_key', table_name='notifications')
    op.drop_index('ix_notifications_status', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
    notification_type.drop(op.get_bind(), checkfirst=True)
    notification_status.drop(op.get_bind(), checkfirst=True)
    notification_priority.drop(op.get_bind(), checkfirst=True)
    notification_entity_type.drop(op.get_bind(), checkfirst=True)
