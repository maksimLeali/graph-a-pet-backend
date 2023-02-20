from utils.logger import logger
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
from api.medias.queries import * 
from api.medias.mutations import * 
from api.treatments.queries import * 
from api.treatments.mutations import * 
from api.treatments.resolvers import treatment
from api.reports.queries import * 
from api.reports.mutations import * 
from api.reports.resolvers import report
from api.statistics.queries import * 
from api.damnationes_memoriae.queries import * 
from api.damnationes_memoriae.mutation import * 
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
query.set_field("getReport", get_report_resolver)
query.set_field("listReports", list_reports_resolver)
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
mutation.set_field("createReport", create_report_resolver)
mutation.set_field("updateReport", update_report_resolver)
mutation.set_field("updateMedia", update_media_resolver)
mutation.set_field("createMedia", create_media_resolver)
mutation.set_field("restoreMemoriae", restore_memoriae_resolver)

object_types = [query, mutation, user, pet, ownership, pet_body, coat, health_card, treatment, report]
