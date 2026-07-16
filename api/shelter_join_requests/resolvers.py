from ariadne import ObjectType

import domain.shelters as shelters_domain
import domain.users as users_domain

shelter_join_request = ObjectType("ShelterJoinRequest")
shelter_join_request.set_field("shelter", lambda obj, info: shelters_domain.get_shelter(obj["shelter_id"]))
shelter_join_request.set_field("user", lambda obj, info: users_domain.get_user(obj["user_id"]))
shelter_join_request.set_field(
    "reviewed_by",
    lambda obj, info: users_domain.get_user(obj["reviewed_by"]) if obj.get("reviewed_by") else None,
)
