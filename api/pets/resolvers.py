from ariadne import ObjectType
from domain.pets import  get_pet_ownerships


pet = ObjectType("Pet")
pet.set_field("ownerships", get_pet_ownerships)