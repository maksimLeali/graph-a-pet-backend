"""Shelter donation settings.

`donations_enabled` and `default_pet_monthly_limit_cents` are per-shelter
persisted settings (on StripeConnectedAccount) — the latter falls back to
the global platform default (stripe config) when unset for a shelter, and
is itself overridable per-pet via PetDonationPolicy.custom_monthly_limit_cents
(see domain/donations/limits.get_effective_limit_cents for the full
fallback chain). `platform_fee_percent` stays a global config value (task:
"the platform fee must not be hardcoded", with a stated global default),
and "unused-funds policy" has no field anywhere in the task's fixed
10-model list.
"""
from api.errors import NotFoundError
import domain.donations.accounts as accounts_domain
from stripe_connect import get_platform_fee_percent, get_default_pet_monthly_limit_cents, get_environment

UNSET = object()  # distinguishes "field not sent" (skip) from "sent as null" (clear to global default)

UNUSED_FUNDS_POLICY_TEXT = (
	"Funds raised beyond a pet's stated need, or after a funding need is "
	"closed, remain in the shelter's general Stripe balance — Graph-a-Pet "
	"never automatically redirects a pet-targeted donation elsewhere."
)


def get_shelter_donation_settings(shelter_id):
	account = accounts_domain.get_active_account_for_shelter(shelter_id)
	if account is None:
		raise NotFoundError(f"no Stripe connected account for shelter {shelter_id}")
	return {
		"donations_enabled": account.donations_enabled,
		"default_pet_monthly_limit_cents": (
			account.default_pet_monthly_limit_cents
			if account.default_pet_monthly_limit_cents is not None
			else get_default_pet_monthly_limit_cents()
		),
		"platform_fee_percent": get_platform_fee_percent(),
		"unused_funds_policy": UNUSED_FUNDS_POLICY_TEXT,
		"environment": get_environment(),
		"connected_account": account.to_dict(),
	}


def update_shelter_donation_settings(shelter_id, donations_enabled=None, default_pet_monthly_limit_cents=UNSET):
	if donations_enabled is not None:
		accounts_domain.set_donations_enabled(shelter_id, donations_enabled)
	if default_pet_monthly_limit_cents is not UNSET:
		accounts_domain.set_shelter_default_pet_monthly_limit(shelter_id, default_pet_monthly_limit_cents)
	return get_shelter_donation_settings(shelter_id)
