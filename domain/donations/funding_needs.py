from api.errors import BadRequest, NotFoundError, FundingNeedClosedError
import domain.shelters as shelters_domain
import domain.pets as pets_domain
import repository.donations.funding_needs as funding_needs_data


def list_funding_needs(shelter_id, status=None, pet_id=None):
	return [n.to_dict() for n in funding_needs_data.list_funding_needs(shelter_id, status, pet_id)]


def get_funding_need(funding_need_id):
	"""Used by api/donations/mutations.py to look up `shelter_id` before
	authorizing update/close (imperative authorize_from_token pattern,
	same as domain/shelter_tasks.get_shelter_task)."""
	model = funding_needs_data.get_funding_need(funding_need_id)
	if model is None:
		raise NotFoundError(f"no funding need found with id {funding_need_id}")
	return model.to_dict()


def create_funding_need(shelter_id, title, target_amount_cents, description=None, category=None,
						 pet_id=None, currency="usd", starts_at=None, ends_at=None):
	shelters_domain.get_shelter(shelter_id)  # raises NotFoundError if missing
	if pet_id:
		pets_domain.get_pet(pet_id)  # raises NotFoundError if missing
	if not title or not title.strip():
		raise BadRequest("title is required")
	if not isinstance(target_amount_cents, int) or target_amount_cents <= 0:
		raise BadRequest("target_amount_cents must be a positive integer")

	model = funding_needs_data.create_funding_need(
		shelter_id=shelter_id, title=title.strip(), description=description, category=category,
		pet_id=pet_id, currency=currency, target_amount_cents=target_amount_cents,
		starts_at=starts_at, ends_at=ends_at,
	)
	return model.to_dict()


def _get_or_404(funding_need_id):
	model = funding_needs_data.get_funding_need(funding_need_id)
	if model is None:
		raise NotFoundError(f"no funding need found with id {funding_need_id}")
	return model


def update_funding_need(funding_need_id, **fields):
	model = _get_or_404(funding_need_id)
	if model.status.name == "CLOSED":
		raise FundingNeedClosedError("cannot edit a closed funding need")
	updated = funding_needs_data.update_funding_need(funding_need_id, **fields)
	return updated.to_dict()


def close_funding_need(funding_need_id):
	model = _get_or_404(funding_need_id)
	if model.status.name == "CLOSED":
		raise FundingNeedClosedError("funding need is already closed")
	updated = funding_needs_data.close_funding_need(funding_need_id)
	return updated.to_dict()
