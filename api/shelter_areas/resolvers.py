from ariadne import ObjectType
from domain.shelter_areas import get_boxes

shelter_area = ObjectType("ShelterArea")
shelter_area.set_field("boxes", get_boxes)
