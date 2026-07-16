from ariadne import convert_kwargs_to_snake_case

from api.authorization.decorators import require_permission, authorize_from_token
from api.errors import format_error
from domain.authorization.catalog import ShelterPermissions, PlatformPermissions
from utils import get_request_user
from utils.logger import logger

import domain.donations.checkout as checkout_domain
import domain.donations.accounts as accounts_domain
import domain.donations.funding_needs as funding_needs_domain
import domain.donations.limits as limits_domain
import domain.donations.expenses as expenses_domain
import domain.donations.settings as settings_domain
import domain.donations.payment_methods as payment_methods_domain
import domain.donations.platform as platform_domain


def _err(e, token=None):
	logger.error(e)
	return {"success": False, "error": format_error(e, token)}


# ---------------------------------------------------------------------------
# Donor mutations
# ---------------------------------------------------------------------------

@convert_kwargs_to_snake_case
def create_guest_donation_checkout_resolver(obj, info, data):
	"""No auth decorator — guest donors have no account by design. See
	domain/donations/public.get_public_donation_availability for every
	precondition enforced before Stripe is even called."""
	try:
		result = checkout_domain.create_donation_checkout(
			shelter_id=data["shelter_id"], target_type=data["target_type"],
			amount_cents=data["amount_cents"], success_url=data["success_url"],
			currency=data.get("currency") or "usd", pet_id=data.get("pet_id"),
			funding_need_id=data.get("funding_need_id"), donor_email=data["donor_email"],
		)
		return {"success": True, "error": None, **result}
	except Exception as e:
		return _err(e)


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.DONATIONS_CREATE, platform=True)
def create_authenticated_donation_resolver(obj, info, data):
	token = info.context.headers["authorization"]
	try:
		user = get_request_user(token)
		result = checkout_domain.create_donation_checkout(
			shelter_id=data["shelter_id"], target_type=data["target_type"],
			amount_cents=data["amount_cents"], success_url=data["success_url"],
			currency=data.get("currency") or "usd", pet_id=data.get("pet_id"),
			funding_need_id=data.get("funding_need_id"),
			donor_user_id=user["id"], donor_email=user.get("email"),
		)
		return {"success": True, "error": None, **result}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.PAYMENT_METHODS_MANAGE_OWN, platform=True)
def create_payment_method_setup_resolver(obj, info, data):
	token = info.context.headers["authorization"]
	try:
		user = get_request_user(token)
		result = payment_methods_domain.create_payment_method_setup(
			user["id"], user.get("email"), data["success_url"], data["cancel_url"], data["consent_text"],
		)
		return {"success": True, "error": None, **result}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.PAYMENT_METHODS_MANAGE_OWN, platform=True)
def remove_saved_payment_method_resolver(obj, info, id):
	token = info.context.headers["authorization"]
	try:
		user = get_request_user(token)
		payment_methods_domain.remove_payment_method(user["id"], id)
		return {"success": True, "error": None}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.PAYMENT_METHODS_MANAGE_OWN, platform=True)
def set_default_payment_method_resolver(obj, info, id):
	token = info.context.headers["authorization"]
	try:
		user = get_request_user(token)
		pm = payment_methods_domain.set_default_payment_method(user["id"], id)
		return {"success": True, "error": None, "payment_method": pm}
	except Exception as e:
		return _err(e, token)


# ---------------------------------------------------------------------------
# Shelter mutations
# ---------------------------------------------------------------------------

@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.DONATIONS_SETTINGS_MANAGE, shelter_argument="shelter_id")
def start_shelter_stripe_onboarding_resolver(obj, info, shelter_id, refresh_url, return_url):
	try:
		result = accounts_domain.start_onboarding(shelter_id, refresh_url, return_url)
		return {"success": True, "error": None, **result}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.DONATIONS_SETTINGS_MANAGE, shelter_argument="shelter_id")
def refresh_shelter_stripe_account_resolver(obj, info, shelter_id):
	try:
		result = accounts_domain.refresh_account_status(shelter_id)
		return {"success": True, "error": None, **result}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.DONATIONS_SETTINGS_MANAGE, shelter_argument="shelter_id")
def update_shelter_donation_settings_resolver(obj, info, shelter_id, data):
	"""Base decorator requires shelters.donations.settings.manage; toggling
	`donations_enabled` additionally requires the specific enable/disable
	permission (sensitive actions), checked imperatively since a single
	static decorator can't express "different permission depending on the
	value of a field")."""
	token = info.context.headers["authorization"]
	try:
		donations_enabled = data.get("donations_enabled")
		if donations_enabled is not None:
			permission = ShelterPermissions.DONATIONS_ENABLE if donations_enabled else ShelterPermissions.DONATIONS_DISABLE
			authorize_from_token(token, permission, shelter_id)
		default_pet_monthly_limit_cents = (
			data["default_pet_monthly_limit_cents"]
			if "default_pet_monthly_limit_cents" in data
			else settings_domain.UNSET
		)
		settings = settings_domain.update_shelter_donation_settings(
			shelter_id, donations_enabled, default_pet_monthly_limit_cents,
		)
		return {"success": True, "error": None, "settings": settings}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.FUNDING_NEEDS_CREATE, input_argument="data")
def create_funding_need_resolver(obj, info, data):
	try:
		funding_need = funding_needs_domain.create_funding_need(
			shelter_id=data["shelter_id"], title=data["title"], target_amount_cents=data["target_amount_cents"],
			description=data.get("description"), category=data.get("category"), pet_id=data.get("pet_id"),
			currency=data.get("currency") or "usd", starts_at=data.get("starts_at"), ends_at=data.get("ends_at"),
			urgency=data.get("urgency"), is_recurring_monthly=data.get("is_recurring_monthly"),
		)
		return {"success": True, "error": None, "funding_need": funding_need}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
def update_funding_need_resolver(obj, info, id, data):
	token = info.context.headers["authorization"]
	try:
		existing = funding_needs_domain.get_funding_need(id)
		authorize_from_token(token, ShelterPermissions.FUNDING_NEEDS_UPDATE, existing["shelter_id"])
		funding_need = funding_needs_domain.update_funding_need(id, **data)
		return {"success": True, "error": None, "funding_need": funding_need}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
def close_funding_need_resolver(obj, info, id):
	token = info.context.headers["authorization"]
	try:
		existing = funding_needs_domain.get_funding_need(id)
		authorize_from_token(token, ShelterPermissions.FUNDING_NEEDS_CLOSE, existing["shelter_id"])
		funding_need = funding_needs_domain.close_funding_need(id)
		return {"success": True, "error": None, "funding_need": funding_need}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.FUNDING_LIMITS_MANAGE, input_argument="data")
def update_pet_donation_limit_resolver(obj, info, data):
	try:
		policy = limits_domain.set_permanent_limit(
			data["pet_id"], data["shelter_id"], data.get("custom_monthly_limit_cents"),
		)
		return {"success": True, "error": None, "policy": policy}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.FUNDING_LIMITS_OVERRIDE, input_argument="data")
def create_temporary_pet_limit_override_resolver(obj, info, data):
	try:
		policy = limits_domain.set_temporary_override(
			data["pet_id"], data["shelter_id"], data["amount_cents"], data["reason"],
			data.get("effective_at"), data["expires_at"],
		)
		return {"success": True, "error": None, "policy": policy}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.EXPENSES_CREATE, input_argument="data")
def create_shelter_expense_resolver(obj, info, data):
	token = info.context.headers["authorization"]
	try:
		user = get_request_user(token)
		expense = expenses_domain.create_expense(
			data["shelter_id"], data["amount_cents"], data["description"],
			currency=data.get("currency") or "usd", pet_id=data.get("pet_id"),
			funding_need_id=data.get("funding_need_id"), created_by_id=user["id"],
		)
		return {"success": True, "error": None, "expense": expense}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
def update_shelter_expense_resolver(obj, info, id, data):
	token = info.context.headers["authorization"]
	try:
		existing = expenses_domain.get_expense(id)
		authorize_from_token(token, ShelterPermissions.EXPENSES_UPDATE, existing["shelter_id"])
		expense = expenses_domain.update_expense(id, **data)
		return {"success": True, "error": None, "expense": expense}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
def submit_shelter_expense_resolver(obj, info, id):
	token = info.context.headers["authorization"]
	try:
		existing = expenses_domain.get_expense(id)
		authorize_from_token(token, ShelterPermissions.EXPENSES_SUBMIT, existing["shelter_id"])
		expense = expenses_domain.submit_expense(id)
		return {"success": True, "error": None, "expense": expense}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
def approve_shelter_expense_resolver(obj, info, id):
	token = info.context.headers["authorization"]
	try:
		existing = expenses_domain.get_expense(id)
		user = authorize_from_token(token, ShelterPermissions.EXPENSES_APPROVE, existing["shelter_id"])
		expense = expenses_domain.approve_expense(id, user["id"])
		return {"success": True, "error": None, "expense": expense}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
def reject_shelter_expense_resolver(obj, info, id, reason):
	token = info.context.headers["authorization"]
	try:
		existing = expenses_domain.get_expense(id)
		user = authorize_from_token(token, ShelterPermissions.EXPENSES_APPROVE, existing["shelter_id"])
		expense = expenses_domain.reject_expense(id, user["id"], reason)
		return {"success": True, "error": None, "expense": expense}
	except Exception as e:
		return _err(e, token)


# ---------------------------------------------------------------------------
# Platform mutations
# ---------------------------------------------------------------------------

@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.DONATIONS_REFUND, platform=True)
def refund_donation_resolver(obj, info, donation_id, reason=None):
	try:
		donation = platform_domain.refund_donation(donation_id, reason)
		return {"success": True, "error": None, "donation": donation}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.DONATIONS_PARTIAL_REFUND, platform=True)
def partially_refund_donation_resolver(obj, info, donation_id, amount_cents, reason):
	try:
		donation = platform_domain.partially_refund_donation(donation_id, amount_cents, reason)
		return {"success": True, "error": None, "donation": donation}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.DONATIONS_SUSPEND, platform=True)
def suspend_connected_account_resolver(obj, info, connected_account_id):
	try:
		account = platform_domain.suspend_connected_account(connected_account_id)
		return {"success": True, "error": None, "connected_account": account}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.FINANCIAL_LEDGER_RECONCILE, platform=True)
def reconcile_financial_transaction_resolver(obj, info, donation_id):
	try:
		result = platform_domain.reconcile_financial_transaction(donation_id)
		return {"success": True, "error": None, **result}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.WEBHOOKS_RETRY, platform=True)
def retry_stripe_webhook_event_resolver(obj, info, id):
	try:
		event = platform_domain.retry_stripe_webhook_event(id)
		return {"success": True, "error": None, "event": event}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))
