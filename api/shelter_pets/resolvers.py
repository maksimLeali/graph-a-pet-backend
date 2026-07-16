from ariadne import ObjectType
from domain.shelter_pets import get_pet, get_shelter, get_assigned_members, get_assigned_shelter_people

shelter_pet = ObjectType("ShelterPet")
shelter_pet.set_field("pet", get_pet)
shelter_pet.set_field("shelter", get_shelter)
shelter_pet.set_field("assigned_members", get_assigned_members)
shelter_pet.set_field("assigned_shelter_people", get_assigned_shelter_people)
