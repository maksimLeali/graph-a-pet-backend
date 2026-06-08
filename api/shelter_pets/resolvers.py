from ariadne import ObjectType
from domain.shelter_pets import get_pet, get_shelter

shelter_pet = ObjectType("ShelterPet")
shelter_pet.set_field("pet", get_pet)
shelter_pet.set_field("shelter", get_shelter)
