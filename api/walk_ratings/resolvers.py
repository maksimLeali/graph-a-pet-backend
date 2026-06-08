from ariadne import ObjectType

import domain.walk_ratings as walk_ratings_domain

walk_rating = ObjectType("WalkRating")

walk_rating.set_field('walk', walk_ratings_domain.get_walk)
