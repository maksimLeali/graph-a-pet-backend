from ariadne import ObjectType
from domain.shelter_people import (
    get_shelter,
    get_user,
    get_created_by,
    get_archived_by,
)

shelter_person = ObjectType("ShelterPerson")
shelter_person.set_field("shelter", get_shelter)
shelter_person.set_field("user", get_user)
shelter_person.set_field("created_by", get_created_by)
shelter_person.set_field("archived_by", get_archived_by)
