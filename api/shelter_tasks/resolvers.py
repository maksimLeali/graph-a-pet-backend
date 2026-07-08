from ariadne import ObjectType
from domain.shelter_tasks import (
    get_shelter,
    get_shelter_pet,
    get_assigned_to,
    get_completed_by,
    get_recurrence,
)

shelter_task = ObjectType("ShelterTask")
shelter_task.set_field("shelter", get_shelter)
shelter_task.set_field("shelter_pet", get_shelter_pet)
shelter_task.set_field("assigned_to", get_assigned_to)
shelter_task.set_field("completed_by", get_completed_by)
shelter_task.set_field("recurrence", get_recurrence)
