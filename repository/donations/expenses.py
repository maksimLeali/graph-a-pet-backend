import uuid
from datetime import datetime

from repository import db
from repository.donations.models import ShelterExpense, ExpenseStatus
from utils.dates import utc_now


def _new_id():
	return f"{uuid.uuid4()}"


def get_expense(expense_id):
	return db.session.query(ShelterExpense).filter(ShelterExpense.id == expense_id).first()


def list_expenses_for_shelter(shelter_id, status=None):
	q = db.session.query(ShelterExpense).filter(ShelterExpense.shelter_id == shelter_id)
	if status:
		q = q.filter(ShelterExpense.status == ExpenseStatus[status])
	return q.order_by(ShelterExpense.created_at.desc()).all()


def create_expense(shelter_id, amount_cents, description, currency="usd", pet_id=None,
					funding_need_id=None, created_by_id=None):
	model = ShelterExpense(
		id=_new_id(),
		shelter_id=shelter_id,
		pet_id=pet_id,
		funding_need_id=funding_need_id,
		currency=currency,
		amount_cents=amount_cents,
		description=description,
		status=ExpenseStatus.DRAFT,
		created_by_id=created_by_id,
		created_at=utc_now(),
	)
	db.session.add(model)
	db.session.commit()
	return model


def update_draft_expense(expense_id, **fields):
	"""Only DRAFT expenses may be edited — enforced by the domain layer,
	not here (this function just writes whatever it's given)."""
	model = get_expense(expense_id)
	if model is None:
		return None
	for key in ("amount_cents", "description", "pet_id", "funding_need_id"):
		if key in fields and fields[key] is not None:
			setattr(model, key, fields[key])
	model.updated_at = utc_now()
	db.session.commit()
	return model


def submit_expense(expense_id):
	model = get_expense(expense_id)
	if model is None:
		return None
	model.status = ExpenseStatus.SUBMITTED
	model.submitted_at = utc_now()
	model.updated_at = utc_now()
	db.session.commit()
	return model


def approve_expense(expense_id, approved_by_id):
	model = get_expense(expense_id)
	if model is None:
		return None
	model.status = ExpenseStatus.APPROVED
	model.approved_by_id = approved_by_id
	model.approved_at = utc_now()
	model.updated_at = utc_now()
	db.session.commit()
	return model


def reject_expense(expense_id, approved_by_id, reason):
	model = get_expense(expense_id)
	if model is None:
		return None
	model.status = ExpenseStatus.REJECTED
	model.approved_by_id = approved_by_id
	model.approved_at = utc_now()
	model.rejected_reason = reason
	model.updated_at = utc_now()
	db.session.commit()
	return model
