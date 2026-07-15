"""stripe_connect_sample

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-07-13

Two tables for the Stripe Connect sample (stripe_connect/ package):
  * stripe_connected_accounts — local "seller" record -> Stripe account id
    mapping. Onboarding/verification/capability status is never stored
    here; it's always fetched live from the Accounts API.
  * stripe_subscriptions — cached status of a connected account's
    subscription to a platform-level plan, kept in sync via
    stripe_connect/webhooks.py (customer.subscription.updated/deleted).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c5d6e7f8a9b0'
down_revision = 'b4c5d6e7f8a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'stripe_connected_accounts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('contact_email', sa.String(), nullable=False),
        sa.Column('stripe_account_id', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_stripe_connected_accounts_stripe_account_id',
        'stripe_connected_accounts', ['stripe_account_id'], unique=True,
    )

    op.create_table(
        'stripe_subscriptions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=False),
        sa.Column('stripe_account_id', sa.String(), nullable=False),
        sa.Column('price_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='incomplete'),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_stripe_subscriptions_stripe_subscription_id',
        'stripe_subscriptions', ['stripe_subscription_id'], unique=True,
    )
    op.create_index(
        'ix_stripe_subscriptions_stripe_account_id',
        'stripe_subscriptions', ['stripe_account_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_stripe_subscriptions_stripe_account_id', table_name='stripe_subscriptions')
    op.drop_index('ix_stripe_subscriptions_stripe_subscription_id', table_name='stripe_subscriptions')
    op.drop_table('stripe_subscriptions')

    op.drop_index('ix_stripe_connected_accounts_stripe_account_id', table_name='stripe_connected_accounts')
    op.drop_table('stripe_connected_accounts')
