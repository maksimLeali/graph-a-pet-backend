from ariadne import ObjectType
from domain.pets import  get_ownerships, get_body


pet = ObjectType("Pet")
pet.set_field("ownerships", get_ownerships)
pet.set_field("body", get_body)