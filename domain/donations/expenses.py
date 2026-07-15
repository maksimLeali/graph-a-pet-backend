from api.errors import BadRequest, NotFoundError, ExpenseNotEditableError
import domain.shelters as shelters_domain
import repository.donations.expenses as expenses_data


def list_expenses(shelter_id, status=None):
	return [e.to_dict() for e in expenses_data.list_expenses_for_shelter(shelter_id, status)]


def get_expense(expense_id):
	"""Used by api/donations/mutations.py to look up `shelter_id` before
	authorizing update/submit/approve/reject."""
	model = expenses_data.get_expense(expense_id)
	if model is None:
		raise NotFoundError(f"no expense found with id {expense_id}")
	return model.to_dict()


def _get_or_404(expense_id):
	model = expenses_data.get_expense(expense_id)
	if model is None:
		raise NotFoundError(f"no expense found with id {expense_id}")
	return model


def create_expense(shelter_id, amount_cents, description, currency="usd", pet_id=None,
					funding_need_id=None, created_by_id=None):
	shelters_domain.get_shelter(shelter_id)  # raises NotFoundError if missing
	if not isinstance(amount_cents, int) or amount_cents <= 0:
		raise BadRequest("amount_cents must be a positive integer")
	if not description or not description.strip():
		raise BadRequest("description is required")
	model = expenses_data.create_expense(
		shelter_id, amount_cents, description.strip(), currency=currency,
		pet_id=pet_id, funding_need_id=funding_need_id, created_by_id=created_by_id,
	)
	return model.to_dict()


def update_expense(expense_id, **fields):
	"""Only DRAFT expenses may be edited — approved financial records are
	never mutated or deleted (task requirement)."""
	model = _get_or_404(expense_id)
	if model.status.name != "DRAFT":
		raise ExpenseNotEditableError(f"cannot edit an expense in status {model.status.name}")
	updated = expenses_data.update_draft_expense(expense_id, **fields)
	return updated.to_dict()


def submit_expense(expense_id):
	model = _get_or_404(expense_id)
	if model.status.name != "DRAFT":
		raise ExpenseNotEditableError(f"cannot submit an expense in status {model.status.name}")
	updated = expenses_data.submit_expense(expense_id)
	return updated.to_dict()


def approve_expense(expense_id, approved_by_id):
	model = _get_or_404(expense_id)
	if model.status.name != "SUBMITTED":
		raise ExpenseNotEditableError(f"cannot approve an expense in status {model.status.name}")
	updated = expenses_data.approve_expense(expense_id, approved_by_id)
	return updated.to_dict()


def reject_expense(expense_id, approved_by_id, reason):
	model = _get_or_404(expense_id)
	if model.status.name != "SUBMITTED":
		raise ExpenseNotEditableError(f"cannot reject an expense in status {model.status.name}")
	if not reason or not reason.strip():
		raise BadRequest("a rejection reason is required")
	updated = expenses_data.reject_expense(expense_id, approved_by_id, reason.strip())
	return updated.to_dict()
