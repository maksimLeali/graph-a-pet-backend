from math import ceil

from ariadne import convert_kwargs_to_snake_case

from api.authorization.decorators import require_permission, authorize_from_token
from api.errors import format_error, NotFoundError
from domain.authorization.catalog import ShelterPermissions, PlatformPermissions
from utils import get_request_user
from utils.logger import logger

import domain.donations.public as public_domain
import domain.donations.donations as donations_domain
import domain.donations.funding_needs as funding_needs_domain
import domain.donations.limits as limits_domain
import domain.donations.expenses as expenses_domain
import domain.donations.reports as reports_domain
import domain.donations.settings as settings_domain
import domain.donations.payment_methods as payment_methods_domain
import domain.donations.platform as platform_domain


def _err(e, token=None):
	logger.error(e)
	return {"success": False, "error": format_error(e, token)}


def _pagination(common_search, total):
	page = (common_search or {}).get("page") or 0
	page_size = (common_search or {}).get("page_size") or 20
	return {
		"total_items": total,
		"total_pages": ceil(total / page_size) if page_size else 0,
		"current_page": page,
		"page_size": page_size,
	}


# ---------------------------------------------------------------------------
# Public (no authentication)
# ---------------------------------------------------------------------------

@convert_kwargs_to_snake_case
def discover_public_shelters_resolver(obj, info, search=None):
	try:
		items, pagination = public_domain.discover_public_shelters(search)
		return {"success": True, "error": None, "items": items, "pagination": pagination}
	except Exception as e:
		return _err(e)


@convert_kwargs_to_snake_case
def get_public_donation_shelter_resolver(obj, info, shelter_id):
	try:
		return public_domain.get_public_shelter(shelter_id)
	except NotFoundError:
		return None
	except Exception as e:
		logger.error(e)
		return None


@convert_kwargs_to_snake_case
def list_public_shelter_pets_resolver(obj, info, shelter_id):
	try:
		return {"success": True, "error": None, "items": public_domain.list_public_shelter_pets(shelter_id)}
	except Exception as e:
		return _err(e)


@convert_kwargs_to_snake_case
def get_public_shelter_pet_resolver(obj, info, shelter_id, pet_id):
	try:
		return {"success": True, "error": None, "pet": public_domain.get_public_shelter_pet(shelter_id, pet_id)}
	except Exception as e:
		return _err(e)


@convert_kwargs_to_snake_case
def get_public_pet_funding_needs_resolver(obj, info, pet_id):
	try:
		return {"success": True, "error": None, "items": public_domain.get_public_pet_funding_needs(pet_id)}
	except Exception as e:
		return _err(e)


@convert_kwargs_to_snake_case
def get_public_donation_availability_resolver(obj, info, shelter_id, pet_id=None, funding_need_id=None):
	try:
		availability = public_domain.get_public_donation_availability(shelter_id, pet_id, funding_need_id)
		return {"success": True, "error": None, "availability": availability}
	except Exception as e:
		return _err(e)


# ---------------------------------------------------------------------------
# Donor (authenticated) — platform.donations.read_own / payment_methods.read_own
# ---------------------------------------------------------------------------

@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.DONATIONS_READ_OWN, platform=True)
def list_my_donations_resolver(obj, info, common_search=None):
	token = info.context.headers["authorization"]
	try:
		user = get_request_user(token)
		page = (common_search or {}).get("page") or 0
		page_size = (common_search or {}).get("page_size") or 20
		items, total = donations_domain.list_my_donations(user["id"], page, page_size)
		return {"success": True, "error": None, "items": items, "pagination": _pagination(common_search, total)}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.DONATIONS_READ_OWN, platform=True)
def get_my_donation_status_resolver(obj, info, donation_id):
	token = info.context.headers["authorization"]
	try:
		user = get_request_user(token)
		donation = donations_domain.get_my_donation(user["id"], donation_id)
		return {"success": True, "error": None, "donation": donation}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.PAYMENT_METHODS_READ_OWN, platform=True)
def list_my_saved_payment_methods_resolver(obj, info):
	token = info.context.headers["authorization"]
	try:
		user = get_request_user(token)
		return {"success": True, "error": None, "items": payment_methods_domain.list_payment_methods(user["id"])}
	except Exception as e:
		return _err(e, token)


# ---------------------------------------------------------------------------
# Shelter operations
# ---------------------------------------------------------------------------

@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.DONATIONS_READ, shelter_argument="shelter_id")
def get_shelter_donation_overview_resolver(obj, info, shelter_id):
	try:
		return {"success": True, "error": None, "overview": reports_domain.get_shelter_donation_overview(shelter_id)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.DONATIONS_READ, shelter_argument="shelter_id")
def list_shelter_donations_resolver(obj, info, shelter_id, common_search=None):
	try:
		page = (common_search or {}).get("page") or 0
		page_size = (common_search or {}).get("page_size") or 20
		order_by = (common_search or {}).get("order_by") or "created_at"
		order_direction = (common_search or {}).get("order_direction") or "desc"
		items, total = donations_domain.list_shelter_donations(shelter_id, page, page_size, order_by, order_direction)
		return {"success": True, "error": None, "items": items, "pagination": _pagination(common_search, total)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.FUNDING_NEEDS_READ, shelter_argument="shelter_id")
def list_funding_needs_resolver(obj, info, shelter_id, status=None):
	try:
		return {"success": True, "error": None, "items": funding_needs_domain.list_funding_needs(shelter_id, status)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.FUNDING_LIMITS_READ, shelter_argument="shelter_id")
def list_pet_donation_policies_resolver(obj, info, shelter_id):
	try:
		return {"success": True, "error": None, "items": limits_domain.list_policies_for_shelter(shelter_id)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
def get_pet_donation_limit_history_resolver(obj, info, pet_id):
	"""No shelter_id argument in the schema (history is keyed by pet only)
	— the shelter_id needed for authorization is derived from the pet's
	current active shelter assignment."""
	token = info.context.headers["authorization"]
	try:
		import repository.donations.shelter_pets as shelter_pets_data
		shelter_pet = shelter_pets_data.get_active_shelter_pet(pet_id)
		if shelter_pet is None:
			raise NotFoundError(f"pet {pet_id} is not currently assigned to a shelter")
		authorize_from_token(token, ShelterPermissions.FUNDING_LIMITS_READ, shelter_pet.shelter_id)
		return {"success": True, "error": None, "items": limits_domain.get_limit_history(pet_id)}
	except Exception as e:
		return _err(e, token)


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.EXPENSES_READ, shelter_argument="shelter_id")
def list_shelter_expenses_resolver(obj, info, shelter_id, status=None):
	try:
		return {"success": True, "error": None, "items": expenses_domain.list_expenses(shelter_id, status)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.DONATIONS_SETTINGS_MANAGE, shelter_argument="shelter_id")
def get_shelter_donation_settings_resolver(obj, info, shelter_id):
	try:
		return {"success": True, "error": None, "settings": settings_domain.get_shelter_donation_settings(shelter_id)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.FINANCIAL_REPORTS_READ, shelter_argument="shelter_id")
def get_shelter_monthly_donation_report_resolver(obj, info, shelter_id, year, month):
	try:
		return {"success": True, "error": None, "report": reports_domain.get_shelter_monthly_report(shelter_id, year, month)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


# ---------------------------------------------------------------------------
# Platform operations
# ---------------------------------------------------------------------------

@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.DONATIONS_READ, platform=True)
def list_platform_donations_resolver(obj, info, common_search=None, shelter_id=None, status=None, donor_type=None):
	try:
		page = (common_search or {}).get("page") or 0
		page_size = (common_search or {}).get("page_size") or 20
		order_by = (common_search or {}).get("order_by") or "created_at"
		order_direction = (common_search or {}).get("order_direction") or "desc"
		items, total = platform_domain.list_platform_donations(
			page, page_size, shelter_id, status, donor_type, order_by, order_direction,
		)
		return {"success": True, "error": None, "items": items, "pagination": _pagination(common_search, total)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.DISPUTES_READ, platform=True)
def list_disputes_resolver(obj, info, common_search=None):
	try:
		page = (common_search or {}).get("page") or 0
		page_size = (common_search or {}).get("page_size") or 20
		items, total = platform_domain.list_disputes(page, page_size)
		return {"success": True, "error": None, "items": items, "pagination": _pagination(common_search, total)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.CONNECTED_ACCOUNTS_READ, platform=True)
def list_connected_accounts_resolver(obj, info, environment=None):
	try:
		return {"success": True, "error": None, "items": platform_domain.list_connected_accounts(environment)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.FINANCIAL_LEDGER_READ, platform=True)
def list_financial_movements_resolver(obj, info, common_search=None, shelter_id=None, movement_type=None):
	try:
		page = (common_search or {}).get("page") or 0
		page_size = (common_search or {}).get("page_size") or 50
		items, total = platform_domain.list_financial_movements(page, page_size, shelter_id, movement_type)
		return {"success": True, "error": None, "items": items, "pagination": _pagination(common_search, total)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.WEBHOOKS_READ, platform=True)
def list_stripe_webhook_events_resolver(obj, info, common_search=None, status=None, event_type=None):
	try:
		page = (common_search or {}).get("page") or 0
		page_size = (common_search or {}).get("page_size") or 50
		items, total = platform_domain.list_stripe_webhook_events(page, page_size, status, event_type)
		return {"success": True, "error": None, "items": items, "pagination": _pagination(common_search, total)}
	except Exception as e:
		return _err(e, info.context.headers.get("authorization"))
