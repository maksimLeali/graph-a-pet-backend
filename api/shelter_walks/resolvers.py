from ariadne import ObjectType
from domain.shelter_walks import get_shelter_pet, get_walker, get_walker_shelter_person
from domain.shelter_walk_ratings import get_ratings_for_shelter_walk

shelter_walk = ObjectType("ShelterWalk")
shelter_walk.set_field("shelter_pet", get_shelter_pet)
shelter_walk.set_field("walker", get_walker)
shelter_walk.set_field("walker_shelter_person", get_walker_shelter_person)
shelter_walk.set_field("ratings", get_ratings_for_shelter_walk)
