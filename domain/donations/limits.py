"""Atomic pet donation limit reservations.

A payment must never be created past a pet's remaining monthly allowance
(task requirement) — so the allowance is reserved BEFORE the Stripe
Checkout Session is created, inside a Postgres advisory-lock-guarded
critical section (see repository/donations/limits.acquire_pet_period_lock),
which makes two concurrent donation attempts for the same pet+month safe:
whichever commits its reservation first shrinks the remaining allowance the
second one sees.
"""
from datetime import datetime, timedelta, timezone
import calendar

try:
	from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - py3.9 ships zoneinfo, kept defensive
	ZoneInfo = None

from api.errors import DonationExceedsPetLimitError
import repository.donations.limits as limits_data
import repository.donations.accounts as accounts_data
from stripe_connect import get_default_pet_monthly_limit_cents, get_environment

RESERVATION_TTL_MINUTES = 15


def _shelter_tz(timezone_name):
	if not ZoneInfo:
		return timezone.utc
	try:
		return ZoneInfo(timezone_name or "UTC")
	except Exception:
		return ZoneInfo("UTC")


def get_period_bounds(now_utc_naive, shelter_timezone):
	"""Shelter-local calendar month boundaries, returned as naive
	UTC-equivalent datetimes (this codebase stores naive DateTime columns
	throughout, all implicitly UTC — see repository/__init__.py Base)."""
	tz = _shelter_tz(shelter_timezone)
	now_aware = now_utc_naive.replace(tzinfo=timezone.utc)
	local_now = now_aware.astimezone(tz)

	start_local = local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
	last_day = calendar.monthrange(start_local.year, start_local.month)[1]
	end_local = start_local.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

	period_start = start_local.astimezone(timezone.utc).replace(tzinfo=None)
	period_end = end_local.astimezone(timezone.utc).replace(tzinfo=None)
	return period_start, period_end


def _shelter_default_limit_cents(shelter_id):
	"""Shelter-level default (StripeConnectedAccount.default_pet_monthly_limit_cents)
	if the shelter has one configured, else the global platform default."""
	account = accounts_data.get_active_connected_account(shelter_id, get_environment().upper())
	if account is not None and account.default_pet_monthly_limit_cents is not None:
		return account.default_pet_monthly_limit_cents
	return get_default_pet_monthly_limit_cents()


def get_effective_limit_cents(pet_id, shelter_id, now=None):
	"""Currently-effective temporary override, else the pet's permanent
	custom limit, else the shelter's default, else the global platform
	default. Never combines them."""
	now = now or datetime.utcnow()
	policy = limits_data.get_policy_for_pet(pet_id)
	if policy is None:
		return _shelter_default_limit_cents(shelter_id), None

	if (
		policy.temporary_override_cents is not None
		and (policy.temporary_override_effective_at is None or policy.temporary_override_effective_at <= now)
		and (policy.temporary_override_expires_at is None or policy.temporary_override_expires_at > now)
	):
		return policy.temporary_override_cents, policy.temporary_override_reason

	if policy.custom_monthly_limit_cents is not None:
		return policy.custom_monthly_limit_cents, None

	return _shelter_default_limit_cents(shelter_id), None


def get_remaining_allowance_cents(pet_id, shelter_id, shelter_timezone, now=None):
	now = now or datetime.utcnow()
	period_start, period_end = get_period_bounds(now, shelter_timezone)
	limit_cents, _ = get_effective_limit_cents(pet_id, shelter_id, now)
	reserved = limits_data.sum_active_reservations(pet_id, period_start, now)
	return {
		"limit_cents": limit_cents,
		"reserved_cents": reserved,
		"remaining_cents": max(limit_cents - reserved, 0),
		"period_start": period_start,
		"period_end": period_end,
	}


def reserve_pet_allowance(pet_id, shelter_id, shelter_timezone, amount_cents, now=None):
	"""Raises DonationExceedsPetLimitError if `amount_cents` would exceed
	the pet's remaining monthly allowance; otherwise inserts and returns a
	new ACTIVE DonationLimitReservation. Must be called BEFORE creating the
	Stripe Checkout Session for a PET-targeted donation."""
	now = now or datetime.utcnow()
	period_start, period_end = get_period_bounds(now, shelter_timezone)

	# held for the rest of this DB transaction — serializes concurrent
	# reservation attempts for this exact pet+period
	limits_data.acquire_pet_period_lock(pet_id, period_start)

	limit_cents, override_reason = get_effective_limit_cents(pet_id, shelter_id, now)
	reserved = limits_data.sum_active_reservations(pet_id, period_start, now)
	remaining = limit_cents - reserved

	if amount_cents > remaining:
		raise DonationExceedsPetLimitError(
			f"donation of {amount_cents} cents exceeds this pet's remaining monthly "
			f"allowance of {max(remaining, 0)} cents"
		)

	expires_at = now + timedelta(minutes=RESERVATION_TTL_MINUTES)
	return limits_data.create_reservation(
		pet_id=pet_id, shelter_id=shelter_id, period_start=period_start, period_end=period_end,
		amount_cents=amount_cents, expires_at=expires_at, override_reason=override_reason,
	)


def consume_reservation(reservation_id, donation_id):
	"""Called once a donation succeeds (webhook-confirmed) — the reserved
	amount becomes a permanent part of the pet's month usage."""
	return limits_data.mark_reservation_consumed(reservation_id, donation_id)


def release_reservation(reservation_id):
	"""Called when a checkout fails/is canceled/expires without ever
	succeeding — frees the held allowance for other donations."""
	return limits_data.release_reservation(reservation_id)


def release_reservation_on_refund(reservation_id, refunded_amount_cents, full_amount_cents):
	"""A full refund frees the pet's allowance back up (the donation no
	longer "counts" against the month); a partial refund does not — the
	pet still received the un-refunded portion. Per the task: refunds must
	be handled by the limit system, not just the ledger."""
	if refunded_amount_cents >= full_amount_cents:
		release_reservation(reservation_id)


def get_limit_history(pet_id):
	"""Reservation history doubles as "limit history" for this pet — see
	the design note in repository/donations/models.py::PetDonationPolicy
	on why there's no dedicated override-log table."""
	return [r.to_dict() for r in limits_data.list_reservation_history_for_pet(pet_id)]


def set_permanent_limit(pet_id, shelter_id, custom_monthly_limit_cents):
	return limits_data.upsert_custom_limit(pet_id, shelter_id, custom_monthly_limit_cents).to_dict()


def set_temporary_override(pet_id, shelter_id, amount_cents, reason, effective_at, expires_at):
	from api.errors import BadRequest
	if not reason or not reason.strip():
		raise BadRequest("a reason is required for a temporary limit override")
	if not expires_at:
		raise BadRequest("an expiration date is required for a temporary limit override")
	return limits_data.upsert_temporary_override(
		pet_id, shelter_id, amount_cents, reason.strip(), effective_at, expires_at,
	).to_dict()


def list_policies_for_shelter(shelter_id):
	return [p.to_dict() for p in limits_data.list_policies_for_shelter(shelter_id)]
