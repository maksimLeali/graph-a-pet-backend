from ariadne import ObjectType
from domain.shelter_claim_requests import get_shelter, get_requester, get_reviewed_by

shelter_claim_request = ObjectType("ShelterClaimRequest")
shelter_claim_request.set_field("shelter", get_shelter)
shelter_claim_request.set_field("requester", get_requester)
shelter_claim_request.set_field("reviewed_by", get_reviewed_by)
