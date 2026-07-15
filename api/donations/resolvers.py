"""Field-level resolvers for donation types that mask sensitive data
depending on the caller's permissions — donor identity and the raw Stripe
account id are never returned to an unprivileged caller, regardless of
what the base dict contains."""
from ariadne import ObjectType

from domain.authorization import authorization_service
from domain.authorization.catalog import ShelterPermissions, PlatformPermissions
from utils import get_request_user


def _current_user_id(info):
	token = info.context.headers.get("authorization")
	if not token:
		return None
	try:
		return get_request_user(token)["id"]
	except Exception:
		return None


def _mask_account_id(stripe_account_id):
	if not stripe_account_id or len(stripe_account_id) < 8:
		return None
	return f"{stripe_account_id[:8]}{'*' * 8}{stripe_account_id[-4:]}"


def resolve_donor_email(obj, info):
	"""Anonymous/guest donor identity stays hidden unless the caller holds
	shelters.donations.read_details (on this donation's shelter) or
	platform.donations.read_details."""
	user_id = _current_user_id(info)
	if not user_id:
		return None
	shelter_id = obj.get("shelter_id")
	if shelter_id and authorization_service.can(
		user_id, ShelterPermissions.DONATIONS_READ_DETAILS, shelter_id=shelter_id
	):
		return obj.get("donor_email")
	if authorization_service.can(user_id, PlatformPermissions.DONATIONS_READ_DETAILS):
		return obj.get("donor_email")
	return None


def resolve_stripe_account_id(obj, info):
	"""Never expose the full stripe_account_id to callers without
	elevated permission — masked otherwise (never in a public URL either,
	see domain/donations/routes for the storefront-id comment)."""
	user_id = _current_user_id(info)
	shelter_id = obj.get("shelter_id")
	raw = obj.get("stripe_account_id")
	if user_id and shelter_id and authorization_service.can(
		user_id, ShelterPermissions.DONATIONS_SETTINGS_MANAGE, shelter_id=shelter_id
	):
		return raw
	if user_id and authorization_service.can(user_id, PlatformPermissions.CONNECTED_ACCOUNTS_READ):
		return raw
	return _mask_account_id(raw)


donation = ObjectType("Donation")
donation.set_field("donor_email", resolve_donor_email)

stripe_connected_account = ObjectType("StripeConnectedAccount")
stripe_connected_account.set_field("stripe_account_id", resolve_stripe_account_id)
