"""Public (no authentication) donation-discovery queries.

Reuses `domain.shelters.discover_shelters` / `get_public_shelter` directly
— those domain functions are themselves auth-free; the existing
`discoverShelters`/`getPublicShelter` GraphQL resolvers only *look* public
because `@auth_middleware` is layered on top of them at the resolver level
(see api/shelters/queries.py). This module's resolvers apply no such
decorator, so they are genuinely public, as the task requires for guest
donors.
"""
from api.errors import NotFoundError
import domain.shelters as shelters_domain
import repository.shelters as shelters_data
import domain.pets as pets_domain
import repository.donations.shelter_pets as shelter_pets_data
import repository.donations.funding_needs as funding_needs_data
import repository.donations.accounts as accounts_data
import domain.donations.limits as limits_domain
from stripe_connect import get_environment


def discover_public_shelters(search=None):
	return shelters_domain.discover_shelters(search or {})


def get_public_shelter(shelter_id):
	shelter = shelters_domain.get_public_shelter(shelter_id)
	if not shelter:
		raise NotFoundError("shelter not found")
	return shelter


def _get_full_public_shelter(shelter_id):
	"""Internal use only — same PUBLIC+VERIFIED filter as
	`get_public_shelter` above, but the full row (has `timezone`, needed
	for pet-limit period math) instead of the narrower PublicShelter
	projection."""
	shelter = shelters_data.get_public_shelter(shelter_id)
	if not shelter:
		raise NotFoundError("shelter not found")
	return shelter


def list_public_shelter_pets(shelter_id):
	_get_full_public_shelter(shelter_id)  # raises if shelter isn't public/verified
	shelter_pets = shelter_pets_data.list_published_shelter_pets(shelter_id)
	pets = []
	for sp in shelter_pets:
		try:
			pet = pets_domain.get_pet(sp.pet_id)
		except NotFoundError:
			continue
		pet["shelter_pet_id"] = sp.id
		pets.append(pet)
	return pets


def get_public_shelter_pet(shelter_id, pet_id):
	_get_full_public_shelter(shelter_id)
	shelter_pet = shelter_pets_data.get_active_shelter_pet(pet_id, shelter_id)
	if shelter_pet is None or not shelter_pet.is_published:
		raise NotFoundError("pet not found")
	pet = pets_domain.get_pet(pet_id)
	pet["shelter_pet_id"] = shelter_pet.id
	return pet


def get_public_pet_funding_needs(pet_id):
	shelter_pet = shelter_pets_data.get_active_shelter_pet(pet_id)
	if shelter_pet is None or not shelter_pet.is_published:
		raise NotFoundError("pet not found")
	return [n.to_dict() for n in funding_needs_data.list_active_funding_needs_for_pet(pet_id)]


def get_public_donation_availability(shelter_id, pet_id=None, funding_need_id=None):
	"""Every precondition from the task's "Public donation operations must
	still enforce" list, in one place — used internally by the guest/auth
	checkout flow AND exposed directly as `getPublicDonationAvailability`
	so the frontend can show/hide the donate button without guessing.
	Never distinguishes "shelter doesn't exist" from "shelter exists but
	isn't public" in the reasons list — that would leak the existence of
	private shelters to unauthenticated callers."""
	reasons = []

	try:
		shelter = _get_full_public_shelter(shelter_id)
	except NotFoundError:
		shelter = None
		reasons.append("SHELTER_NOT_AVAILABLE")

	account = accounts_data.get_active_connected_account(shelter_id, get_environment().upper()) if shelter else None
	if shelter and account is None:
		reasons.append("CONNECTED_ACCOUNT_MISSING")
	elif account:
		if not account.donations_enabled:
			reasons.append("SHELTER_DONATIONS_DISABLED")
		if not account.charges_enabled:
			reasons.append("STRIPE_CHARGES_NOT_ENABLED")

	remaining_cents = None
	limit_cents = None
	if pet_id:
		shelter_pet = shelter_pets_data.get_active_shelter_pet(pet_id, shelter_id)
		if shelter_pet is None or not shelter_pet.is_published:
			reasons.append("PET_NOT_PUBLISHED")
		if shelter:
			allowance = limits_domain.get_remaining_allowance_cents(pet_id, shelter_id, shelter.get("timezone") or "UTC")
			remaining_cents = allowance["remaining_cents"]
			# exposed alongside remaining so the app can render a monthly
			# progress bar (raised = limit - remaining) and the goal-reached
			# celebration state — see the app's DonateCard
			limit_cents = allowance["limit_cents"]
			if remaining_cents <= 0:
				reasons.append("PET_LIMIT_REACHED")

	if funding_need_id:
		need = funding_needs_data.get_funding_need(funding_need_id)
		if need is None or need.status.name != "ACTIVE":
			reasons.append("FUNDING_NEED_NOT_ACTIVE")

	return {
		"available": len(reasons) == 0,
		"reasons": reasons,
		"remaining_pet_allowance_cents": remaining_cents,
		"pet_monthly_limit_cents": limit_cents,
		"is_test_mode": get_environment() == "test",
	}
