from ariadne import ObjectType
from domain.ownerships import  get_pet, get_user


ownership = ObjectType("Ownership")
ownership.set_field("pet", get_pet)
ownership.set_field("user", get_user)