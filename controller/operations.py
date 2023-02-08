from utils.logger import logger
from ariadne import QueryType, MutationType
from controller.users.resolvers import user
from controller.users.queries import *
from controller.users.mutations import *
from controller.pets.resolvers import pet
from controller.pets.queries import *
from controller.pets.mutations import *
from controller.ownerships.resolvers import ownership
from controller.ownerships.queries import *
from controller.ownerships.mutations import *
from controller.pet_bodies.resolvers import pet_body
from controller.pet_bodies.queries import *
from controller.pet_bodies.mutations import *
from controller.coats.resolvers import coat
from controller.coats.queries import *
from controller.coats.mutations import *
from controller.health_cards.queries import * 
from controller.health_cards.mutations import * 
from controller.health_cards.resolvers import health_card
from controller.medias.queries import * 
from controller.medias.mutations import * 
from controller.treatments.queries import * 
from controller.treatments.mutations import * 
from controller.treatments.resolvers import treatment
from controller.statistics.queries import * 
from controller.damnationes_memoriae.queries import * 
from controller.damnationes_memoriae.mutation import * 
from domain import refresh_token
from controller.middlewares import auth_middleware

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
query.set_field("listMedias", list_medias_resolver)
query.set_field("getMedia", get_media_resolver)
query.set_field("getDashboard", dashboard_resolver)
query.set_field("getRealTimeStatistic", get_real_time_statistic_resolver)
query.set_field("getGroupedStatistics", get_statistics_by_group)
query.set_field("listDamnationesMemoriae", list_damnationes_memoriae_resolver)

mutation = MutationType()
mutation.set_field('createUser', create_user_resolver)
mutation.set_field('signUp', signup_resolver)
mutation.set_field('updateUser', update_user_resolver)
mutation.set_field('deleteUser', delete_user_resolver)
mutation.set_field('updateMe', update_me_resolver)
mutation.set_field('login', login_resolver)
mutation.set_field('createPet', create_pet_resolver)
mutation.set_field('updatePet', update_pet_resolver)
mutation.set_field('deletePet', delete_pet_resolver)
mutation.set_field('deleteOwnership', delete_ownership_resolver)
mutation.set_field('addPetToUser', add_pet_to_user_resolver)
mutation.set_field('addPetToMe', add_pet_to_me_resolver)
mutation.set_field('updateOwnership', update_ownership_resolver)
mutation.set_field("refreshToken", refresh_token_resolver)
mutation.set_field("updateHealthCard", update_health_card_resolver)
mutation.set_field("createHealthCard", create_health_card_resolver)
mutation.set_field("createTreatment", create_treatment_resolver)
mutation.set_field("updateTreatment", update_treatment_resolver)
mutation.set_field("updateMedia", update_media_resolver)
mutation.set_field("createMedia", create_media_resolver)
mutation.set_field("restoreMemoriae", restore_memoriae_resolver)

object_types = [query, mutation, user, pet, ownership, pet_body, coat, health_card, treatment]
