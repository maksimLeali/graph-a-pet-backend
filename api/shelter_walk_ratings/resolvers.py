from ariadne import ObjectType
import domain.shelter_walk_ratings as shelter_walk_ratings_domain

shelter_walk_rating = ObjectType("ShelterWalkRating")
shelter_walk_rating.set_field('walk', shelter_walk_ratings_domain.get_shelter_walk)
