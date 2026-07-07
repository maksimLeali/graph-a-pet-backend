from ariadne import ObjectType
from domain.shelter_zones import get_areas, get_boxes

shelter_zone = ObjectType("ShelterZone")
shelter_zone.set_field("areas", get_areas)
shelter_zone.set_field("boxes", get_boxes)
