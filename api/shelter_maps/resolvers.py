from ariadne import ObjectType
from domain.shelter_maps import get_shelter, get_background_media, get_boxes, get_areas, get_elements

shelter_map = ObjectType("ShelterMap")
shelter_map.set_field("shelter", get_shelter)
shelter_map.set_field("background_media", get_background_media)
shelter_map.set_field("boxes", get_boxes)
shelter_map.set_field("areas", get_areas)
shelter_map.set_field("elements", get_elements)
