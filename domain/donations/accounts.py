"""Shelter Stripe Connect onboarding — orchestrates the SAME Stripe API
calls verified in the stripe_connect/ sample (reused directly, not
reimplemented): `create_connected_account`, `get_account_status`,
`create_onboarding_account_link` from stripe_connect/service.py.
"""
from datetime import datetime

from api.errors import NotFoundError
import domain.shelters as shelters_domain
import repository.donations.accounts as accounts_data
from stripe_connect import get_environment
from stripe_connect.service import (
	create_connected_account as _stripe_create_connected_account,
	get_account_status as _stripe_get_account_status,
	create_onboarding_account_link as _stripe_create_account_link,
)


def get_active_account_for_shelter(shelter_id):
	return accounts_data.get_active_connected_account(shelter_id, get_environment().upper())


def start_onboarding(shelter_id, refresh_url, return_url):
	"""Creates the connected account on first call (idempotent per
	shelter+environment thanks to the partial-unique index), then always
	returns a fresh Account Link — Stripe onboarding links are single-use
	and short-lived, so "resume onboarding" is just "create a new link"."""
	shelter = shelters_domain.get_shelter(shelter_id)  # raises NotFoundError if missing

	account = get_active_account_for_shelter(shelter_id)
	if account is None:
		stripe_account = _stripe_create_connected_account(
			display_name=shelter["name"], contact_email=shelter.get("public_contact_email") or "",
		)
		account = accounts_data.create_connected_account(
			shelter_id=shelter_id, stripe_account_id=stripe_account.id,
			environment=get_environment().upper(),
		)

	link = _stripe_create_account_link(account.stripe_account_id, refresh_url, return_url)
	return {"connected_account": account.to_dict(), "onboarding_url": link.url}


def refresh_account_status(shelter_id):
	"""Always re-reads the Accounts API live (per the task: status is never
	authoritative from a cache) and refreshes the denormalized columns used
	for list views."""
	account = get_active_account_for_shelter(shelter_id)
	if account is None:
		raise NotFoundError(f"no Stripe connected account for shelter {shelter_id}")

	status = _stripe_get_account_status(account.stripe_account_id)
	stripe_account = status["account"]

	updated = accounts_data.update_account_status(
		account.id,
		onboarding_status="complete" if status["onboarding_complete"] else "incomplete",
		verification_status="verified" if status["ready_to_process_payments"] else "unverified",
		charges_enabled=status["ready_to_process_payments"],
		payouts_enabled=bool(getattr(stripe_account, "payouts_enabled", False)),
		details_submitted=bool(status["onboarding_complete"]),
	)
	return {
		"connected_account": updated.to_dict(),
		"requirements": status["requirements"],
	}


def set_donations_enabled(shelter_id, enabled: bool):
	account = get_active_account_for_shelter(shelter_id)
	if account is None:
		raise NotFoundError(f"no Stripe connected account for shelter {shelter_id}")
	if enabled and not account.charges_enabled:
		from api.errors import StripeChargesNotEnabledError
		raise StripeChargesNotEnabledError(
			"cannot enable donations before Stripe onboarding is complete and charges are enabled"
		)
	return accounts_data.set_donations_enabled(account.id, enabled)


def set_shelter_default_pet_monthly_limit(shelter_id, cents):
	account = get_active_account_for_shelter(shelter_id)
	if account is None:
		raise NotFoundError(f"no Stripe connected account for shelter {shelter_id}")
	if cents is not None and cents < 0:
		from api.errors import InvalidDonationAmountError
		raise InvalidDonationAmountError("default_pet_monthly_limit_cents cannot be negative")
	return accounts_data.set_default_pet_monthly_limit(account.id, cents)
