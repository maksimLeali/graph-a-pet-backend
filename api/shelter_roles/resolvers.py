from ariadne import ObjectType
from domain.shelter_roles import get_user, get_shelter

shelter_role = ObjectType("ShelterRole")
shelter_role.set_field("user", get_user)
shelter_role.set_field("shelter", get_shelter)
