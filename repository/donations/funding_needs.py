import uuid
from datetime import datetime

from repository import db
from repository.donations.models import PetFundingNeed, FundingNeedStatus


def _new_id():
	return f"{uuid.uuid4()}"


def get_funding_need(funding_need_id):
	return db.session.query(PetFundingNeed).filter(PetFundingNeed.id == funding_need_id).first()


def list_funding_needs(shelter_id, status=None, pet_id=None):
	q = db.session.query(PetFundingNeed).filter(PetFundingNeed.shelter_id == shelter_id)
	if status:
		q = q.filter(PetFundingNeed.status == FundingNeedStatus[status])
	if pet_id:
		q = q.filter(PetFundingNeed.pet_id == pet_id)
	return q.order_by(PetFundingNeed.created_at.desc()).all()


def list_active_funding_needs_for_pet(pet_id):
	return db.session.query(PetFundingNeed).filter(
		PetFundingNeed.pet_id == pet_id,
		PetFundingNeed.status == FundingNeedStatus.ACTIVE,
	).all()


def create_funding_need(shelter_id, title, description=None, category=None, pet_id=None,
						 currency="usd", target_amount_cents=0, starts_at=None, ends_at=None):
	model = PetFundingNeed(
		id=_new_id(),
		shelter_id=shelter_id,
		pet_id=pet_id,
		title=title,
		description=description,
		category=category,
		currency=currency,
		target_amount_cents=target_amount_cents,
		starts_at=starts_at,
		ends_at=ends_at,
		created_at=datetime.utcnow(),
	)
	db.session.add(model)
	db.session.commit()
	return model


def update_funding_need(funding_need_id, **fields):
	model = get_funding_need(funding_need_id)
	if model is None:
		return None
	for key in ("title", "description", "category", "target_amount_cents", "starts_at", "ends_at"):
		if key in fields and fields[key] is not None:
			setattr(model, key, fields[key])
	model.updated_at = datetime.utcnow()
	db.session.commit()
	return model


def close_funding_need(funding_need_id):
	model = get_funding_need(funding_need_id)
	if model is None:
		return None
	model.status = FundingNeedStatus.CLOSED
	model.closed_at = datetime.utcnow()
	model.updated_at = datetime.utcnow()
	db.session.commit()
	return model


def increment_collected_amount(funding_need_id, amount_cents):
	"""Called only from a webhook-confirmed SUCCEEDED donation — never from
	a Checkout redirect. See domain/donations/webhooks.py."""
	model = get_funding_need(funding_need_id)
	if model is None:
		return None
	model.collected_amount_cents = (model.collected_amount_cents or 0) + amount_cents
	model.updated_at = datetime.utcnow()
	db.session.commit()
	return model
