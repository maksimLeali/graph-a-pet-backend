from ariadne import ObjectType
from domain.pets import  get_ownerships


pet = ObjectType("Pet")
pet.set_field("ownerships", get_ownerships)