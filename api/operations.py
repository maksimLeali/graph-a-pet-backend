from libs.logger import logger
from ariadne import QueryType, MutationType
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
from api.health_cards.queries import * 
from api.health_cards.mutations import * 
from api.health_cards.resolvers import health_card
from api.treatments.queries import * 
from api.treatments.mutations import * 
from api.treatments.resolvers import treatment
from domain import refresh_token
from api.middlewares import auth_middleware

@auth_middleware
def refresh_token_resolver(obj, info):
    logger.info("API | operation.py | refresh token")
    logger.debug(info.context.headers)
    token = info.context.headers['Authorization']
    refreshed_token= refresh_token(token)
    try:
        payload = {
            "success": True,
            "token": refreshed_token
        }
    except Exception as e:
        payload = {
            "success": False,
            "token": "",
            "errors": str(e)
        }

    return payload


query = QueryType()
query.set_field("listUsers", list_users_resolver)
query.set_field("getUser", get_user_resolver)
query.set_field("listPets", list_pets_resolver)
query.set_field("getPet", get_pet_resolver)
query.set_field("me", me_resolver)
query.set_field("getOwnership", get_ownership_resolver)
query.set_field("listOwnerships", list_ownerships_resolver)
query.set_field("listHealthCards", list_health_cards_resolver)
query.set_field("getHealthCard", get_health_card_resolver)
query.set_field("getTreatment", get_treatment_resolver)
query.set_field("listTreatments", list_treatments_resolver)

mutation = MutationType()
mutation.set_field('createUser', create_user_resolver)
mutation.set_field('signUp', signup_resolver)
mutation.set_field('updateUser', update_user_resolver)
mutation.set_field('login', login_resolver)
mutation.set_field('createPet', create_pet_resolver)
mutation.set_field('updatePet', update_pet_resolver)
mutation.set_field('addPetToUser', add_pet_to_user_resolver)
mutation.set_field('addPetToMe', add_pet_to_me_resolver)
mutation.set_field('updateOwnership', update_ownership_resolver)
mutation.set_field("refreshToken", refresh_token_resolver)
mutation.set_field("updateHealthCard", update_health_card_resolver)
mutation.set_field("createHealthCard", create_health_card_resolver)
mutation.set_field("createTreatment", create_treatment_resolver)
mutation.set_field("updateTreatment", update_treatment_resolver)

object_types = [query, mutation, user, pet, ownership, pet_body, coat, health_card, treatment]
