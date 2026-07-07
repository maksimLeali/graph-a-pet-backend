from ariadne import ObjectType
from domain.shelter_boxes import (
    get_area,
    get_zone,
    get_status,
    get_current_occupants,
    get_occupancy_history,
)

shelter_box = ObjectType("ShelterBox")
shelter_box.set_field("area", get_area)
shelter_box.set_field("zone", get_zone)
shelter_box.set_field("status", get_status)
shelter_box.set_field("current_occupants", get_current_occupants)
shelter_box.set_field("occupancy_history", get_occupancy_history)
