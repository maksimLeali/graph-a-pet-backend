from ariadne import ObjectType
from domain.shelter_invites import get_user, get_shelter, get_invited_by

shelter_invite = ObjectType("ShelterInvite")
shelter_invite.set_field("user", get_user)
shelter_invite.set_field("shelter", get_shelter)
shelter_invite.set_field("invited_by", get_invited_by)
