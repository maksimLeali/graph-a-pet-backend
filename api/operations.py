from ariadne import ObjectType
from api.users.queries import *
from api.users.mutations import *
from api.pets.mutations import *
from api.pets.queries import *
from api.users.resolvers import user
from api.pets.resolvers import pet


query = ObjectType("Query")
query.set_field("listUsers", list_users_resolver)
query.set_field("getUser", get_user_resolver)
query.set_field("listPets", list_pets_resolver)
query.set_field("getPet", get_pet_resolver)

mutation = ObjectType("Mutation")
mutation.set_field('createUser', create_user_resolver)
mutation.set_field('updateUser', update_user_resolver)
mutation.set_field('createPet', create_pet_resolver)
mutation.set_field('updatePet', update_pet_resolver)

object_types = [query, mutation, user, pet]