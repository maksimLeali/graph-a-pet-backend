from ariadne import ObjectType
from api.users.resolvers import user
from api.users.queries import *
from api.users.mutations import *
from api.pets.resolvers import pet
from api.pets.queries import *
from api.pets.mutations import *
from api.ownerships.resolvers import ownership
from api.ownerships.queries import *
from api.ownerships.mutations import *
from api.pet_bodies.resolvers import pet_body
from api.pet_bodies.queries import *
from api.pet_bodies.mutations import *
from api.coats.resolvers import coat
from api.coats.queries import *
from api.coats.mutations import *


query = ObjectType("Query")
query.set_field("listUsers", list_users_resolver)
query.set_field("getUser", get_user_resolver)
query.set_field("listPets", list_pets_resolver)
query.set_field("getPet", get_pet_resolver)
query.set_field("getOwnership", get_ownership_resolver)
query.set_field("listOwnerships", list_ownerships_resolver)

mutation = ObjectType("Mutation")
mutation.set_field('createUser', create_user_resolver)
mutation.set_field('updateUser', update_user_resolver)
mutation.set_field('login', login_resolver)
mutation.set_field('createPet', create_pet_resolver)
mutation.set_field('updatePet', update_pet_resolver)
mutation.set_field('addPetToUser', add_pet_to_user_resolver)
mutation.set_field('updateOwnership', update_ownership_resolver)

object_types = [query, mutation, user, pet, ownership, pet_body, coat]