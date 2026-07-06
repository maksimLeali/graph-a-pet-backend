from ariadne import ObjectType
from domain.shelter_occupancies import get_box, get_shelter_pet, get_moved_by

shelter_box_occupancy = ObjectType("ShelterBoxOccupancy")
shelter_box_occupancy.set_field("box", get_box)
shelter_box_occupancy.set_field("shelter_pet", get_shelter_pet)
shelter_box_occupancy.set_field("moved_by", get_moved_by)
