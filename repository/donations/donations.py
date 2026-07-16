import uuid
from datetime import datetime

from repository import db
from repository.donations.models import Donation, DonationStatus, RefundStatus, DisputeStatus
from utils.dates import utc_now


def _new_id():
	return f"{uuid.uuid4()}"


def get_donation(donation_id):
	return db.session.query(Donation).filter(Donation.id == donation_id).first()


def get_donation_by_payment_intent(stripe_payment_intent_id):
	return db.session.query(Donation).filter(
		Donation.stripe_payment_intent_id == stripe_payment_intent_id
	).first()


def get_donation_by_checkout_session(stripe_checkout_session_id):
	return db.session.query(Donation).filter(
		Donation.stripe_checkout_session_id == stripe_checkout_session_id
	).first()


def create_pending_donation(*, shelter_id, connected_account_id, target_type, donor_type,
							 gross_amount_cents, platform_fee_percent, currency="usd",
							 pet_id=None, funding_need_id=None, reservation_id=None,
							 donor_user_id=None, donor_email=None, is_test=True,
							 stripe_checkout_session_id=None):
	platform_fee_amount_cents = round(gross_amount_cents * platform_fee_percent / 100)
	model = Donation(
		id=_new_id(),
		shelter_id=shelter_id,
		connected_account_id=connected_account_id,
		target_type=target_type,
		pet_id=pet_id,
		funding_need_id=funding_need_id,
		reservation_id=reservation_id,
		donor_type=donor_type,
		donor_user_id=donor_user_id,
		donor_email=donor_email,
		currency=currency,
		gross_amount_cents=gross_amount_cents,
		platform_fee_percent=platform_fee_percent,
		platform_fee_amount_cents=platform_fee_amount_cents,
		status=DonationStatus.PENDING,
		is_test=is_test,
		stripe_checkout_session_id=stripe_checkout_session_id,
		created_at=utc_now(),
	)
	db.session.add(model)
	db.session.commit()
	return model


def set_checkout_session_id(donation_id, stripe_checkout_session_id):
	model = get_donation(donation_id)
	if model is None:
		return None
	model.stripe_checkout_session_id = stripe_checkout_session_id
	model.updated_at = utc_now()
	db.session.commit()
	return model


def mark_processing(donation_id, stripe_payment_intent_id):
	model = get_donation(donation_id)
	if model is None:
		return None
	model.status = DonationStatus.PROCESSING
	model.stripe_payment_intent_id = stripe_payment_intent_id
	model.updated_at = utc_now()
	db.session.commit()
	return model


def mark_succeeded(donation_id, *, processing_fee_amount_cents, shelter_net_amount_cents,
					stripe_payment_intent_id=None):
	model = get_donation(donation_id)
	if model is None:
		return None
	model.status = DonationStatus.SUCCEEDED
	model.processing_fee_amount_cents = processing_fee_amount_cents
	model.shelter_net_amount_cents = shelter_net_amount_cents
	if stripe_payment_intent_id:
		model.stripe_payment_intent_id = stripe_payment_intent_id
	model.updated_at = utc_now()
	db.session.commit()
	return model


def list_stale_pending_donations(cutoff):
	"""Donations still PENDING after the app's poll timeout — see
	domain/donations/donations.expire_stale_pending_donations."""
	return db.session.query(Donation).filter(
		Donation.status == DonationStatus.PENDING, Donation.created_at < cutoff,
	).all()


def mark_failed(donation_id):
	model = get_donation(donation_id)
	if model is None:
		return None
	model.status = DonationStatus.FAILED
	model.updated_at = utc_now()
	db.session.commit()
	return model


def mark_canceled(donation_id):
	model = get_donation(donation_id)
	if model is None:
		return None
	model.status = DonationStatus.CANCELED
	model.updated_at = utc_now()
	db.session.commit()
	return model


def apply_refund(donation_id, refunded_amount_cents, full: bool):
	model = get_donation(donation_id)
	if model is None:
		return None
	model.refunded_amount_cents = refunded_amount_cents
	model.refund_status = RefundStatus.FULL if full else RefundStatus.PARTIAL
	model.updated_at = utc_now()
	db.session.commit()
	return model


def set_dispute_status(donation_id, status: str):
	model = get_donation(donation_id)
	if model is None:
		return None
	model.dispute_status = DisputeStatus[status]
	model.updated_at = utc_now()
	db.session.commit()
	return model


def list_donations_for_shelter(shelter_id, page=0, page_size=20, order_by="created_at", order_direction="desc"):
	q = db.session.query(Donation).filter(Donation.shelter_id == shelter_id)
	total = q.count()
	column = getattr(Donation, order_by, Donation.created_at)
	column = column.desc() if order_direction == "desc" else column.asc()
	items = q.order_by(column).offset(page * page_size).limit(page_size).all()
	return items, total


def list_donations_platform(page=0, page_size=20, shelter_id=None, status=None, donor_type=None,
							 order_by="created_at", order_direction="desc"):
	q = db.session.query(Donation)
	if shelter_id:
		q = q.filter(Donation.shelter_id == shelter_id)
	if status:
		q = q.filter(Donation.status == DonationStatus[status])
	if donor_type:
		from repository.donations.models import DonorType
		q = q.filter(Donation.donor_type == DonorType[donor_type])
	total = q.count()
	column = getattr(Donation, order_by, Donation.created_at)
	column = column.desc() if order_direction == "desc" else column.asc()
	items = q.order_by(column).offset(page * page_size).limit(page_size).all()
	return items, total


def list_donations_for_user(donor_user_id, page=0, page_size=20):
	q = db.session.query(Donation).filter(Donation.donor_user_id == donor_user_id)
	total = q.count()
	items = q.order_by(Donation.created_at.desc()).offset(page * page_size).limit(page_size).all()
	return items, total
