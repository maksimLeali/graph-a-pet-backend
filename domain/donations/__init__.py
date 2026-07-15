"""Graph-a-Pet donation domain — business logic layer.

Split by concern: accounts.py (onboarding), limits.py (atomic pet
allowance reservations), checkout.py (guest/authenticated donation
creation), webhooks.py (event processing + ledger), funding_needs.py,
expenses.py, reports.py (shelter overview aggregation), public.py (public
discovery/availability), payment_methods.py (donor saved cards).

Every function here calls repository.donations.* + other domains
(domain.shelters, domain.pets) — never touches SQLAlchemy directly, and
raises the api.errors DomainError subclasses added for this feature
(DonationExceedsPetLimitError, ShelterNotVerifiedError, etc.) — same
layering convention as domain/shelter_tasks.
"""
from utils import get_request_user
from stripe_connect import get_environment


def get_optional_user(token):
	"""Guest donation mutations accept both authenticated and anonymous
	callers — unlike `get_request_user`, this returns None instead of
	raising when there's no valid token (see the "General Tips" in the
	research this domain was built from: no existing helper in this
	codebase already does this, so it lives here)."""
	if not token:
		return None
	try:
		return get_request_user(token)
	except Exception:
		return None


def assert_test_mode_object(livemode: bool, what="object"):
	"""The whole feature is test-only right now — refuse to process a
	livemode=true Stripe object/event regardless of which key is
	configured. See stripe_connect.StripeTestModeError for the equivalent
	guard on the secret key itself."""
	from api.errors import BadRequest
	if livemode and get_environment() == "test":
		raise BadRequest(f"received a livemode=true {what} while running in test mode; rejected")
