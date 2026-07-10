from ariadne import ObjectType
from domain.shelter_tasks import (
    get_shelter,
    get_shelter_pet,
    get_assignees,
    get_assignee_shelter_people,
    get_completed_by,
    get_skipped_by,
    get_recurrence,
)

shelter_task = ObjectType("ShelterTask")
shelter_task.set_field("shelter", get_shelter)
shelter_task.set_field("shelter_pet", get_shelter_pet)
shelter_task.set_field("assignees", get_assignees)
shelter_task.set_field("assignee_shelter_people", get_assignee_shelter_people)
shelter_task.set_field("completed_by", get_completed_by)
shelter_task.set_field("skipped_by", get_skipped_by)
shelter_task.set_field("recurrence", get_recurrence)
