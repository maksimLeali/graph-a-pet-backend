"""Read-only helpers against the existing ShelterPet model (owned by
repository/shelter_pets/) — kept here rather than added to that package to
keep this feature's footprint contained to repository/donations/."""
from repository import db
from repository.shelter_pets.models import ShelterPet


def get_active_shelter_pet(pet_id, shelter_id=None):
	q = db.session.query(ShelterPet).filter(
		ShelterPet.pet_id == pet_id, ShelterPet.is_active.is_(True),
	)
	if shelter_id:
		q = q.filter(ShelterPet.shelter_id == shelter_id)
	return q.first()


def list_published_shelter_pets(shelter_id):
	return db.session.query(ShelterPet).filter(
		ShelterPet.shelter_id == shelter_id,
		ShelterPet.is_active.is_(True),
		ShelterPet.is_published.is_(True),
	).all()
