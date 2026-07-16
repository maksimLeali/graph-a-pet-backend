"""Thin domain wrappers around repository/donations/donations.py list
queries — shelter-scoped and donor-scoped (platform-scoped listing lives
in domain/donations/platform.py alongside the other platform operations)."""
from datetime import datetime, timedelta

from api.errors import NotFoundError
import domain.donations.limits as limits_domain
import repository.donations.donations as donations_data
from utils.dates import utc_now

# app polls a donation's status for at most this long (see the pending-
# confirmation screen); a donation still PENDING past this age never
# succeeded (webhook never showed up — abandoned/failed Stripe session) and
# is swept FAILED by the cron:minutely job in schedules/donations.py
PENDING_TIMEOUT_MINUTES = 10


def get_donation(donation_id):
	model = donations_data.get_donation(donation_id)
	if model is None:
		raise NotFoundError(f"no donation found with id {donation_id}")
	return model.to_dict()


def get_my_donation(donor_user_id, donation_id):
	"""Owner-scoped read used by the app's pending-confirmation poll — a
	donation belonging to someone else 404s exactly like a missing one, it
	never leaks existence to a caller who isn't its donor."""
	model = donations_data.get_donation(donation_id)
	if model is None or model.donor_user_id != donor_user_id:
		raise NotFoundError(f"no donation found with id {donation_id}")
	return model.to_dict()


def list_shelter_donations(shelter_id, page=0, page_size=20, order_by="created_at", order_direction="desc"):
	items, total = donations_data.list_donations_for_shelter(
		shelter_id, page=page, page_size=page_size, order_by=order_by, order_direction=order_direction,
	)
	return [d.to_dict() for d in items], total


def list_my_donations(donor_user_id, page=0, page_size=20):
	items, total = donations_data.list_donations_for_user(donor_user_id, page=page, page_size=page_size)
	return [d.to_dict() for d in items], total


def expire_stale_pending_donations(now=None):
	"""Sweep donations stuck PENDING past PENDING_TIMEOUT_MINUTES — a
	legitimate success always arrives as payment_intent.succeeded well
	before this (webhook-confirmed, see domain/donations/webhooks.py), so a
	donation still PENDING here was abandoned or Stripe never got back to
	us. Mirrors handle_payment_intent_failed: mark FAILED + release any pet
	allowance reservation so it doesn't hold up the pet's monthly limit."""
	cutoff = (now or utc_now()) - timedelta(minutes=PENDING_TIMEOUT_MINUTES)
	stale = donations_data.list_stale_pending_donations(cutoff)
	for donation in stale:
		donations_data.mark_failed(donation.id)
		if donation.reservation_id:
			limits_domain.release_reservation(donation.reservation_id)
	return len(stale)
