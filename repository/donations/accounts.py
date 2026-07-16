import uuid
from datetime import datetime

from repository import db
from repository.donations.models import StripeConnectedAccount, ConnectedAccountEnvironment
from utils.dates import utc_now


def _new_id():
	return f"{uuid.uuid4()}"


def get_active_connected_account(shelter_id, environment="TEST"):
	return db.session.query(StripeConnectedAccount).filter(
		StripeConnectedAccount.shelter_id == shelter_id,
		StripeConnectedAccount.environment == ConnectedAccountEnvironment[environment],
		StripeConnectedAccount.is_active.is_(True),
	).first()


def get_connected_account_by_id(connected_account_id):
	return db.session.query(StripeConnectedAccount).filter(
		StripeConnectedAccount.id == connected_account_id
	).first()


def get_connected_account_by_stripe_id(stripe_account_id):
	return db.session.query(StripeConnectedAccount).filter(
		StripeConnectedAccount.stripe_account_id == stripe_account_id
	).first()


def create_connected_account(shelter_id, stripe_account_id, environment="TEST"):
	model = StripeConnectedAccount(
		id=_new_id(),
		shelter_id=shelter_id,
		stripe_account_id=stripe_account_id,
		environment=ConnectedAccountEnvironment[environment],
		is_active=True,
		created_at=utc_now(),
	)
	db.session.add(model)
	db.session.commit()
	return model


def update_account_status(connected_account_id, *, onboarding_status=None, verification_status=None,
						   charges_enabled=None, payouts_enabled=None, details_submitted=None):
	"""Refresh the denormalized status cache from a live Accounts API read
	(or an account.updated webhook) — never invented, always sourced from
	Stripe. `last_synced_at` marks when this happened."""
	model = get_connected_account_by_id(connected_account_id)
	if model is None:
		return None
	if onboarding_status is not None:
		model.onboarding_status = onboarding_status
	if verification_status is not None:
		model.verification_status = verification_status
	if charges_enabled is not None:
		model.charges_enabled = charges_enabled
	if payouts_enabled is not None:
		model.payouts_enabled = payouts_enabled
	if details_submitted is not None:
		model.details_submitted = details_submitted
	model.last_synced_at = utc_now()
	model.updated_at = utc_now()
	db.session.commit()
	return model


def set_donations_enabled(connected_account_id, enabled: bool):
	model = get_connected_account_by_id(connected_account_id)
	if model is None:
		return None
	model.donations_enabled = enabled
	model.updated_at = utc_now()
	db.session.commit()
	return model


def set_default_pet_monthly_limit(connected_account_id, cents):
	"""cents=None clears the shelter override back to the global default."""
	model = get_connected_account_by_id(connected_account_id)
	if model is None:
		return None
	model.default_pet_monthly_limit_cents = cents
	model.updated_at = utc_now()
	db.session.commit()
	return model


def list_connected_accounts(environment=None):
	"""Platform-wide list — used by `listConnectedAccounts`."""
	q = db.session.query(StripeConnectedAccount).filter(StripeConnectedAccount.is_active.is_(True))
	if environment:
		q = q.filter(StripeConnectedAccount.environment == ConnectedAccountEnvironment[environment])
	return q.order_by(StripeConnectedAccount.created_at.desc()).all()
