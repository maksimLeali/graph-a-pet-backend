from ariadne import ObjectType
from domain.shelter_ownership_transfers import get_shelter, get_from_user, get_to_user

shelter_ownership_transfer = ObjectType("ShelterOwnershipTransfer")
shelter_ownership_transfer.set_field("shelter", get_shelter)
shelter_ownership_transfer.set_field("from_user", get_from_user)
shelter_ownership_transfer.set_field("to_user", get_to_user)
