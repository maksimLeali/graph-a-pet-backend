"""Plain DB access helpers for the Stripe Connect sample models.

Mirrors the small, direct-query style used by repository/authorization —
no ORM relationships, just query/insert helpers the routes call directly.
"""
import uuid
from datetime import datetime

from repository import db
from stripe_connect.models import StripeConnectedAccount, StripeSubscription


def _new_id():
	return f"{uuid.uuid4()}"


def list_connected_accounts():
	return db.session.query(StripeConnectedAccount).order_by(
		StripeConnectedAccount.created_at.desc()
	).all()


def get_connected_account(seller_id):
	return db.session.query(StripeConnectedAccount).filter(
		StripeConnectedAccount.id == seller_id
	).first()


def get_connected_account_by_stripe_id(stripe_account_id):
	return db.session.query(StripeConnectedAccount).filter(
		StripeConnectedAccount.stripe_account_id == stripe_account_id
	).first()


def create_connected_account_record(display_name, contact_email, stripe_account_id):
	"""Store the mapping from our local "seller" record to the Stripe
	account id — the only thing about the account we persist. Everything
	else (onboarding/verification/capability status) is always re-fetched
	live from the Accounts API, per the task's instructions."""
	model = StripeConnectedAccount(
		id=_new_id(),
		display_name=display_name,
		contact_email=contact_email,
		stripe_account_id=stripe_account_id,
		created_at=datetime.utcnow(),
	)
	db.session.add(model)
	db.session.commit()
	return model


def upsert_subscription(stripe_subscription_id, stripe_account_id, price_id, status,
						 cancel_at_period_end=False):
	"""Idempotent upsert driven by webhook events — see
	stripe_connect/webhooks.py `handle_subscription_updated`."""
	model = db.session.query(StripeSubscription).filter(
		StripeSubscription.stripe_subscription_id == stripe_subscription_id
	).first()
	if model is None:
		model = StripeSubscription(
			id=_new_id(),
			stripe_subscription_id=stripe_subscription_id,
			created_at=datetime.utcnow(),
		)
		db.session.add(model)
	model.stripe_account_id = stripe_account_id
	model.price_id = price_id
	model.status = status
	model.cancel_at_period_end = cancel_at_period_end
	model.updated_at = datetime.utcnow()
	db.session.commit()
	return model


def get_subscription_for_account(stripe_account_id):
	"""Most recent subscription row for a connected account (a real
	integration would likely support several, but one is enough for this
	demo's "Subscribe" button)."""
	return db.session.query(StripeSubscription).filter(
		StripeSubscription.stripe_account_id == stripe_account_id
	).order_by(StripeSubscription.created_at.desc()).first()


def delete_subscription(stripe_subscription_id):
	db.session.query(StripeSubscription).filter(
		StripeSubscription.stripe_subscription_id == stripe_subscription_id
	).delete()
	db.session.commit()
