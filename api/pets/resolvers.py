from ariadne import ObjectType
from domain.pets import  get_ownerships, get_coat


pet = ObjectType("Pet")
pet.set_field("ownerships", get_ownerships)
pet.set_field("coat", get_coat)