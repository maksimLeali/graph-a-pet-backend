"""Append-only ledger data access. No update/delete functions exist here on
purpose — corrections are new compensating rows (see
domain/donations/ledger.py)."""
import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from repository import db
from repository.donations.models import FinancialMovement, MovementType


def _new_id():
	return f"{uuid.uuid4()}"


def record_movement(*, shelter_id, movement_type: str, amount_cents, donation_id=None,
					 stripe_object_id=None, currency="usd", description=None, is_test=True):
	"""Idempotent insert: replaying the same (donation_id, movement_type,
	stripe_object_id) tuple from a redelivered webhook is a no-op, not a
	duplicate ledger entry — enforced by the DB unique constraint."""
	model = FinancialMovement(
		id=_new_id(),
		shelter_id=shelter_id,
		donation_id=donation_id,
		movement_type=MovementType[movement_type],
		amount_cents=amount_cents,
		currency=currency,
		stripe_object_id=stripe_object_id,
		description=description,
		is_test=is_test,
		created_at=datetime.utcnow(),
	)
	db.session.add(model)
	try:
		db.session.commit()
		return model, True
	except IntegrityError:
		db.session.rollback()
		return None, False


def list_movements_for_shelter(shelter_id, page=0, page_size=50, movement_type=None):
	q = db.session.query(FinancialMovement).filter(FinancialMovement.shelter_id == shelter_id)
	if movement_type:
		q = q.filter(FinancialMovement.movement_type == MovementType[movement_type])
	total = q.count()
	items = q.order_by(FinancialMovement.created_at.desc()).offset(page * page_size).limit(page_size).all()
	return items, total


def list_movements_platform(page=0, page_size=50, shelter_id=None, movement_type=None):
	q = db.session.query(FinancialMovement)
	if shelter_id:
		q = q.filter(FinancialMovement.shelter_id == shelter_id)
	if movement_type:
		q = q.filter(FinancialMovement.movement_type == MovementType[movement_type])
	total = q.count()
	items = q.order_by(FinancialMovement.created_at.desc()).offset(page * page_size).limit(page_size).all()
	return items, total


def list_movements_for_donation(donation_id):
	return db.session.query(FinancialMovement).filter(
		FinancialMovement.donation_id == donation_id
	).order_by(FinancialMovement.created_at.asc()).all()


def sum_by_type(shelter_id, start=None, end=None):
	"""{movement_type_name: total_amount_cents} for a shelter, optionally
	windowed — used by domain/donations/reports.py for the overview and
	monthly-summary aggregates. Never used to derive per-donation
	financial facts from anything other than webhook-confirmed movements."""
	q = db.session.query(
		FinancialMovement.movement_type, func.coalesce(func.sum(FinancialMovement.amount_cents), 0)
	).filter(FinancialMovement.shelter_id == shelter_id)
	if start:
		q = q.filter(FinancialMovement.created_at >= start)
	if end:
		q = q.filter(FinancialMovement.created_at < end)
	rows = q.group_by(FinancialMovement.movement_type).all()
	return {movement_type.name: int(total) for movement_type, total in rows}


def is_balanced(donation_id):
	"""A donation's movements are "balanced" when they net to zero
	(gross - platform_fee - processing_fee - shelter_net = 0, plus any
	refund/reversal pairs). Used by the ledger UI's per-transaction
	balanced/unbalanced indicator."""
	movements = list_movements_for_donation(donation_id)
	return sum(m.amount_cents for m in movements) == 0
