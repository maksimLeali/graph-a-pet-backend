"""donations_core

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-07-13

Full Graph-a-Pet donation domain: connected accounts (shelter-scoped),
donations, ledger (financial_movements), pet funding needs, pet donation
limits + atomic reservations, shelter expenses, webhook idempotency, and
donor payment profiles/methods/consent.

Two relationships are intentionally NOT circular FKs (see
repository/donations/models.py docstring for why): DonationLimitReservation
-> Donation is a plain indexed column, and UserPaymentProfile ->
UserPaymentMethod is a plain indexed column. Every other relationship is a
real FK, enforced by Postgres.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7f8a9b0c1d2'
down_revision = 'd6e7f8a9b0c1'
branch_labels = None
depends_on = None

connected_account_environment = postgresql.ENUM(
    'TEST', 'LIVE', name='connectedaccountenvironment', create_type=False,
)
donation_target_type = postgresql.ENUM(
    'SHELTER', 'PET', 'PET_FUNDING_NEED', name='donationtargettype', create_type=False,
)
donor_type = postgresql.ENUM(
    'GUEST', 'AUTHENTICATED', name='donortype', create_type=False,
)
donation_status = postgresql.ENUM(
    'PENDING', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'CANCELED', name='donationstatus', create_type=False,
)
refund_status = postgresql.ENUM(
    'NONE', 'PARTIAL', 'FULL', name='refundstatus', create_type=False,
)
dispute_status = postgresql.ENUM(
    'NONE', 'OPEN', 'WON', 'LOST', name='disputestatus', create_type=False,
)
movement_type = postgresql.ENUM(
    'GROSS_PAYMENT', 'PLATFORM_FEE', 'PROCESSING_FEE', 'SHELTER_NET',
    'REFUND', 'DISPUTE', 'REVERSAL', 'ADJUSTMENT', name='movementtype', create_type=False,
)
funding_need_status = postgresql.ENUM(
    'ACTIVE', 'CLOSED', name='fundingneedstatus', create_type=False,
)
expense_status = postgresql.ENUM(
    'DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', name='expensestatus', create_type=False,
)
reservation_status = postgresql.ENUM(
    'ACTIVE', 'CONSUMED', 'RELEASED', 'EXPIRED', name='reservationstatus', create_type=False,
)
webhook_event_status = postgresql.ENUM(
    'RECEIVED', 'PROCESSED', 'FAILED', 'IGNORED', name='webhookeventstatus', create_type=False,
)

ALL_ENUMS = [
    connected_account_environment, donation_target_type, donor_type,
    donation_status, refund_status, dispute_status, movement_type,
    funding_need_status, expense_status, reservation_status, webhook_event_status,
]


def upgrade() -> None:
    bind = op.get_bind()

    # The stripe_connect/ sample (migration c5d6e7f8a9b0) created a generic
    # "seller" stripe_connected_accounts table + stripe_subscriptions. This
    # migration REPLACES that seller model with the real, shelter-scoped
    # donation domain (same table name, new shape) and drops the
    # subscription-to-platform-plan feature entirely (out of donation
    # scope per the task). The sample's Python routes are unregistered by
    # default (see stripe_connect.SAMPLE_ENABLED in app.py) specifically
    # because of this table replacement — see docs/stripe-connect-sample.md.
    op.drop_index('ix_stripe_subscriptions_stripe_account_id', table_name='stripe_subscriptions')
    op.drop_index('ix_stripe_subscriptions_stripe_subscription_id', table_name='stripe_subscriptions')
    op.drop_table('stripe_subscriptions')
    op.drop_index('ix_stripe_connected_accounts_stripe_account_id', table_name='stripe_connected_accounts')
    op.drop_table('stripe_connected_accounts')

    for enum_type in ALL_ENUMS:
        enum_type.create(bind, checkfirst=True)

    # --- stripe_connected_accounts (shelter-scoped — see comment above) ---
    op.create_table(
        'stripe_connected_accounts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('stripe_account_id', sa.String(), nullable=False),
        sa.Column('environment', connected_account_environment, nullable=False, server_default='TEST'),
        sa.Column('onboarding_status', sa.String(), nullable=False, server_default='not_started'),
        sa.Column('verification_status', sa.String(), nullable=False, server_default='unverified'),
        sa.Column('charges_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('payouts_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('details_submitted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('donations_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_stripe_connected_accounts_shelter_id', 'stripe_connected_accounts', ['shelter_id'])
    op.create_index('ix_stripe_connected_accounts_stripe_account_id', 'stripe_connected_accounts', ['stripe_account_id'], unique=True)
    op.create_index(
        'ux_stripe_connected_accounts_shelter_env_active', 'stripe_connected_accounts',
        ['shelter_id', 'environment'], unique=True,
        postgresql_where=sa.text('is_active'),
    )

    # --- pet_funding_needs ---
    op.create_table(
        'pet_funding_needs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('pet_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=False, server_default='usd'),
        sa.Column('target_amount_cents', sa.Integer(), nullable=False),
        sa.Column('collected_amount_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', funding_need_status, nullable=False, server_default='ACTIVE'),
        sa.Column('starts_at', sa.DateTime(), nullable=True),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id']),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pet_funding_needs_shelter_id', 'pet_funding_needs', ['shelter_id'])
    op.create_index('ix_pet_funding_needs_pet_id', 'pet_funding_needs', ['pet_id'])

    # --- pet_donation_policies ---
    op.create_table(
        'pet_donation_policies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('pet_id', sa.String(), nullable=False),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('custom_monthly_limit_cents', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id']),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pet_id', name='uq_pet_donation_policies_pet'),
    )
    op.create_index('ix_pet_donation_policies_pet_id', 'pet_donation_policies', ['pet_id'])
    op.create_index('ix_pet_donation_policies_shelter_id', 'pet_donation_policies', ['shelter_id'])

    # --- donation_limit_reservations ---
    op.create_table(
        'donation_limit_reservations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('pet_id', sa.String(), nullable=False),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('status', reservation_status, nullable=False, server_default='ACTIVE'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('override_expires_at', sa.DateTime(), nullable=True),
        sa.Column('donation_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id']),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_donation_limit_reservations_pet_id', 'donation_limit_reservations', ['pet_id'])
    op.create_index('ix_donation_limit_reservations_shelter_id', 'donation_limit_reservations', ['shelter_id'])
    op.create_index('ix_donation_limit_reservations_donation_id', 'donation_limit_reservations', ['donation_id'])
    op.create_index(
        'ix_donation_limit_reservations_active_period', 'donation_limit_reservations',
        ['pet_id', 'period_start', 'status'],
    )

    # --- donations ---
    op.create_table(
        'donations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('connected_account_id', sa.String(), nullable=False),
        sa.Column('target_type', donation_target_type, nullable=False),
        sa.Column('pet_id', sa.String(), nullable=True),
        sa.Column('funding_need_id', sa.String(), nullable=True),
        sa.Column('reservation_id', sa.String(), nullable=True),
        sa.Column('donor_type', donor_type, nullable=False),
        sa.Column('donor_user_id', sa.String(), nullable=True),
        sa.Column('donor_email', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=False, server_default='usd'),
        sa.Column('gross_amount_cents', sa.Integer(), nullable=False),
        sa.Column('platform_fee_percent', sa.Float(), nullable=False),
        sa.Column('platform_fee_amount_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processing_fee_amount_cents', sa.Integer(), nullable=True),
        sa.Column('shelter_net_amount_cents', sa.Integer(), nullable=True),
        sa.Column('status', donation_status, nullable=False, server_default='PENDING'),
        sa.Column('refund_status', refund_status, nullable=False, server_default='NONE'),
        sa.Column('refunded_amount_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dispute_status', dispute_status, nullable=False, server_default='NONE'),
        sa.Column('is_test', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('stripe_checkout_session_id', sa.String(), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id']),
        sa.ForeignKeyConstraint(['connected_account_id'], ['stripe_connected_accounts.id']),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id']),
        sa.ForeignKeyConstraint(['funding_need_id'], ['pet_funding_needs.id']),
        sa.ForeignKeyConstraint(['reservation_id'], ['donation_limit_reservations.id']),
        sa.ForeignKeyConstraint(['donor_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_donations_shelter_id', 'donations', ['shelter_id'])
    op.create_index('ix_donations_pet_id', 'donations', ['pet_id'])
    op.create_index('ix_donations_funding_need_id', 'donations', ['funding_need_id'])
    op.create_index('ix_donations_stripe_checkout_session_id', 'donations', ['stripe_checkout_session_id'])
    op.create_index('ix_donations_stripe_payment_intent_id', 'donations', ['stripe_payment_intent_id'], unique=True)

    # --- financial_movements (append-only ledger) ---
    op.create_table(
        'financial_movements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('donation_id', sa.String(), nullable=True),
        sa.Column('movement_type', movement_type, nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False, server_default='usd'),
        sa.Column('stripe_object_id', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_test', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id']),
        sa.ForeignKeyConstraint(['donation_id'], ['donations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('donation_id', 'movement_type', 'stripe_object_id',
                             name='uq_financial_movements_donation_type_object'),
    )
    op.create_index('ix_financial_movements_shelter_id', 'financial_movements', ['shelter_id'])
    op.create_index('ix_financial_movements_donation_id', 'financial_movements', ['donation_id'])
    op.create_index('ix_financial_movements_movement_type', 'financial_movements', ['movement_type'])
    op.create_index('ix_financial_movements_stripe_object_id', 'financial_movements', ['stripe_object_id'])

    # --- shelter_expenses ---
    op.create_table(
        'shelter_expenses',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('shelter_id', sa.String(), nullable=False),
        sa.Column('pet_id', sa.String(), nullable=True),
        sa.Column('funding_need_id', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=False, server_default='usd'),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', expense_status, nullable=False, server_default='DRAFT'),
        sa.Column('created_by_id', sa.String(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by_id', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id']),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id']),
        sa.ForeignKeyConstraint(['funding_need_id'], ['pet_funding_needs.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shelter_expenses_shelter_id', 'shelter_expenses', ['shelter_id'])
    op.create_index('ix_shelter_expenses_status', 'shelter_expenses', ['status'])

    # --- stripe_webhook_events (append-only) ---
    op.create_table(
        'stripe_webhook_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('stripe_event_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('livemode', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('status', webhook_event_status, nullable=False, server_default='RECEIVED'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('payload', postgresql.JSONB(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_event_id', name='uq_stripe_webhook_events_event_id'),
    )
    op.create_index('ix_stripe_webhook_events_stripe_event_id', 'stripe_webhook_events', ['stripe_event_id'])
    op.create_index('ix_stripe_webhook_events_event_type', 'stripe_webhook_events', ['event_type'])

    # --- user_payment_profiles ---
    op.create_table(
        'user_payment_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=False),
        sa.Column('default_payment_method_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_payment_profiles_user'),
        sa.UniqueConstraint('stripe_customer_id', name='uq_user_payment_profiles_customer'),
    )
    op.create_index('ix_user_payment_profiles_user_id', 'user_payment_profiles', ['user_id'])

    # --- user_payment_methods ---
    op.create_table(
        'user_payment_methods',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_payment_profile_id', sa.String(), nullable=False),
        sa.Column('stripe_payment_method_id', sa.String(), nullable=False),
        sa.Column('card_brand', sa.String(), nullable=True),
        sa.Column('card_last4', sa.String(), nullable=True),
        sa.Column('card_exp_month', sa.Integer(), nullable=True),
        sa.Column('card_exp_year', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(['user_payment_profile_id'], ['user_payment_profiles.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_payment_method_id', name='uq_user_payment_methods_pm'),
    )
    op.create_index('ix_user_payment_methods_profile_id', 'user_payment_methods', ['user_payment_profile_id'])

    # --- payment_method_consents (immutable) ---
    op.create_table(
        'payment_method_consents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_payment_method_id', sa.String(), nullable=False),
        sa.Column('consented_at', sa.DateTime(), nullable=False),
        sa.Column('consent_text', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_payment_method_id'], ['user_payment_methods.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payment_method_consents_pm_id', 'payment_method_consents', ['user_payment_method_id'])


def downgrade() -> None:
    # NOTE: this does not recreate the old sample stripe_connected_accounts/
    # stripe_subscriptions tables dropped in upgrade() — the seller demo
    # schema is considered retired, not reversible back to.
    op.drop_index('ix_payment_method_consents_pm_id', table_name='payment_method_consents')
    op.drop_table('payment_method_consents')

    op.drop_index('ix_user_payment_methods_profile_id', table_name='user_payment_methods')
    op.drop_table('user_payment_methods')

    op.drop_index('ix_user_payment_profiles_user_id', table_name='user_payment_profiles')
    op.drop_table('user_payment_profiles')

    op.drop_index('ix_stripe_webhook_events_event_type', table_name='stripe_webhook_events')
    op.drop_index('ix_stripe_webhook_events_stripe_event_id', table_name='stripe_webhook_events')
    op.drop_table('stripe_webhook_events')

    op.drop_index('ix_shelter_expenses_status', table_name='shelter_expenses')
    op.drop_index('ix_shelter_expenses_shelter_id', table_name='shelter_expenses')
    op.drop_table('shelter_expenses')

    op.drop_index('ix_financial_movements_stripe_object_id', table_name='financial_movements')
    op.drop_index('ix_financial_movements_movement_type', table_name='financial_movements')
    op.drop_index('ix_financial_movements_donation_id', table_name='financial_movements')
    op.drop_index('ix_financial_movements_shelter_id', table_name='financial_movements')
    op.drop_table('financial_movements')

    op.drop_index('ix_donations_stripe_payment_intent_id', table_name='donations')
    op.drop_index('ix_donations_stripe_checkout_session_id', table_name='donations')
    op.drop_index('ix_donations_funding_need_id', table_name='donations')
    op.drop_index('ix_donations_pet_id', table_name='donations')
    op.drop_index('ix_donations_shelter_id', table_name='donations')
    op.drop_table('donations')

    op.drop_index('ix_donation_limit_reservations_active_period', table_name='donation_limit_reservations')
    op.drop_index('ix_donation_limit_reservations_donation_id', table_name='donation_limit_reservations')
    op.drop_index('ix_donation_limit_reservations_shelter_id', table_name='donation_limit_reservations')
    op.drop_index('ix_donation_limit_reservations_pet_id', table_name='donation_limit_reservations')
    op.drop_table('donation_limit_reservations')

    op.drop_index('ix_pet_donation_policies_shelter_id', table_name='pet_donation_policies')
    op.drop_index('ix_pet_donation_policies_pet_id', table_name='pet_donation_policies')
    op.drop_table('pet_donation_policies')

    op.drop_index('ix_pet_funding_needs_pet_id', table_name='pet_funding_needs')
    op.drop_index('ix_pet_funding_needs_shelter_id', table_name='pet_funding_needs')
    op.drop_table('pet_funding_needs')

    op.drop_index('ux_stripe_connected_accounts_shelter_env_active', table_name='stripe_connected_accounts')
    op.drop_index('ix_stripe_connected_accounts_stripe_account_id', table_name='stripe_connected_accounts')
    op.drop_index('ix_stripe_connected_accounts_shelter_id', table_name='stripe_connected_accounts')
    op.drop_table('stripe_connected_accounts')

    bind = op.get_bind()
    for enum_type in reversed(ALL_ENUMS):
        enum_type.drop(bind, checkfirst=True)
