import uuid
from datetime import datetime

from sqlalchemy import func, text

from repository import db
from repository.donations.models import PetDonationPolicy, DonationLimitReservation, ReservationStatus
from utils.dates import utc_now


def _new_id():
	return f"{uuid.uuid4()}"


def get_policy_for_pet(pet_id):
	return db.session.query(PetDonationPolicy).filter(PetDonationPolicy.pet_id == pet_id).first()


def list_policies_for_shelter(shelter_id):
	return db.session.query(PetDonationPolicy).filter(PetDonationPolicy.shelter_id == shelter_id).all()


def upsert_custom_limit(pet_id, shelter_id, custom_monthly_limit_cents):
	model = get_policy_for_pet(pet_id)
	if model is None:
		model = PetDonationPolicy(
			id=_new_id(), pet_id=pet_id, shelter_id=shelter_id, created_at=utc_now(),
		)
		db.session.add(model)
	model.custom_monthly_limit_cents = custom_monthly_limit_cents
	model.updated_at = utc_now()
	db.session.commit()
	return model


def upsert_temporary_override(pet_id, shelter_id, amount_cents, reason, effective_at, expires_at):
	model = get_policy_for_pet(pet_id)
	if model is None:
		model = PetDonationPolicy(
			id=_new_id(), pet_id=pet_id, shelter_id=shelter_id, created_at=utc_now(),
		)
		db.session.add(model)
	model.temporary_override_cents = amount_cents
	model.temporary_override_reason = reason
	model.temporary_override_effective_at = effective_at
	model.temporary_override_expires_at = expires_at
	model.updated_at = utc_now()
	db.session.commit()
	return model


def acquire_pet_period_lock(pet_id, period_start):
	"""Postgres transaction-scoped advisory lock keyed by pet+period —
	blocks concurrent reservation attempts for the SAME pet+month until
	this transaction commits/rolls back. See
	domain/donations/limits.reserve_pet_allowance for why this (rather than
	`SELECT ... FOR UPDATE` on existing rows, which doesn't prevent
	phantom inserts) is the correct primitive here."""
	key = f"pet_limit:{pet_id}:{period_start.isoformat()}"
	db.session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": key})


def sum_active_reservations(pet_id, period_start, now):
	total = db.session.query(func.coalesce(func.sum(DonationLimitReservation.amount_cents), 0)).filter(
		DonationLimitReservation.pet_id == pet_id,
		DonationLimitReservation.period_start == period_start,
		DonationLimitReservation.status == ReservationStatus.ACTIVE,
		DonationLimitReservation.expires_at > now,
	).scalar()
	return int(total or 0)


def create_reservation(pet_id, shelter_id, period_start, period_end, amount_cents, expires_at,
						override_reason=None, override_expires_at=None):
	model = DonationLimitReservation(
		id=_new_id(),
		pet_id=pet_id,
		shelter_id=shelter_id,
		period_start=period_start,
		period_end=period_end,
		amount_cents=amount_cents,
		status=ReservationStatus.ACTIVE,
		expires_at=expires_at,
		override_reason=override_reason,
		override_expires_at=override_expires_at,
		created_at=utc_now(),
	)
	db.session.add(model)
	db.session.commit()
	return model


def get_reservation(reservation_id):
	return db.session.query(DonationLimitReservation).filter(
		DonationLimitReservation.id == reservation_id
	).first()


def mark_reservation_consumed(reservation_id, donation_id):
	model = get_reservation(reservation_id)
	if model is None:
		return None
	model.status = ReservationStatus.CONSUMED
	model.donation_id = donation_id
	model.updated_at = utc_now()
	db.session.commit()
	return model


def release_reservation(reservation_id):
	"""Called when a checkout is abandoned/fails/expires — frees the held
	allowance back up for other donations in the same period."""
	model = get_reservation(reservation_id)
	if model is None or model.status != ReservationStatus.ACTIVE:
		return model
	model.status = ReservationStatus.RELEASED
	model.updated_at = utc_now()
	db.session.commit()
	return model


def list_reservation_history_for_pet(pet_id):
	return db.session.query(DonationLimitReservation).filter(
		DonationLimitReservation.pet_id == pet_id
	).order_by(DonationLimitReservation.created_at.desc()).all()
