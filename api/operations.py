from utils.logger import logger
from ariadne import QueryType, MutationType
from api.users.resolvers import user, dashboard
from api.users.queries import *
from api.users.mutations import *
from api.pets.resolvers import pet
from api.pets.queries import *
from api.pets.mutations import *
from api.ownerships.resolvers import ownership
from api.ownerships.queries import *
from api.ownerships.mutations import *
from api.walks.queries import *
from api.walks.mutations import *
from api.walks.resolvers import walk
from api.walk_ratings.queries import *
from api.walk_ratings.mutations import *
from api.walk_ratings.resolvers import walk_rating
from api.cures.queries import *
from api.cures.mutations import *
from api.cures.resolvers import cure
from api.health_cards.queries import * 
from api.health_cards.mutations import * 
from api.health_cards.resolvers import health_card
from api.medias.queries import * 
from api.medias.mutations import * 
from api.codes.queries import *
from api.codes.mutations import * 
from api.treatments.queries import * 
from api.treatments.mutations import * 
from api.treatments.resolvers import treatment
from api.reports.queries import * 
from api.reports.mutations import * 
from api.reports.resolvers import report
from api.statistics.queries import * 
from api.damnationes_memoriae.queries import * 
from api.damnationes_memoriae.mutation import * 
from api.shelters.queries import *
from api.shelters.mutations import *
from api.shelters.resolvers import shelter
from api.shelter_roles.queries import *
from api.shelter_roles.mutations import *
from api.shelter_roles.resolvers import shelter_role
from api.shelter_pets.queries import *
from api.shelter_pets.mutations import *
from api.shelter_pets.resolvers import shelter_pet
from api.shelter_tasks.queries import *
from api.shelter_tasks.mutations import *
from api.shelter_tasks.resolvers import shelter_task
from api.shelter_walks.queries import *
from api.shelter_walks.mutations import *
from api.shelter_walks.resolvers import shelter_walk
from api.shelter_maps.queries import *
from api.shelter_maps.mutations import *
from api.shelter_maps.resolvers import shelter_map
from api.shelter_boxes.queries import *
from api.shelter_boxes.mutations import *
from api.shelter_boxes.resolvers import shelter_box
from api.shelter_occupancies.queries import *
from api.shelter_occupancies.mutations import *
from api.shelter_occupancies.resolvers import shelter_box_occupancy
from api.shelter_areas.queries import *
from api.shelter_areas.mutations import *
from api.shelter_areas.resolvers import shelter_area
from api.shelter_inventory.queries import *
from api.shelter_inventory.mutations import *
from api.shelter_inventory.resolvers import shelter_inventory_item, shelter_inventory_movement
from api.shelter_map_elements.queries import *
from api.shelter_map_elements.mutations import *
from api.shelter_dashboard.queries import *
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
query.set_field("listMyPets", list_my_pets)
query.set_field("getPet", get_pet_resolver)
query.set_field("me", me_resolver)
query.set_field("getOwnership", get_ownership_resolver)
query.set_field("listOwnerships", list_ownerships_resolver)
query.set_field("listHealthCards", list_health_cards_resolver)
query.set_field("getHealthCard", get_health_card_resolver)
query.set_field("getTreatment", get_treatment_resolver)
query.set_field("listTreatments", list_treatments_resolver)
query.set_field("listMyTreatments", list_my_treatments_resolver)
query.set_field("getReport", get_report_resolver)
query.set_field("listReports", list_reports_resolver)
query.set_field("listMedias", list_medias_resolver)
query.set_field("getMedia", get_media_resolver)
query.set_field("listCodes", list_codes_resolver)
query.set_field("getCode", get_code_resolver)
query.set_field("getDashboard", dashboard_resolver)
query.set_field("getRealTimeStatistic", get_real_time_statistic_resolver)
query.set_field("getGroupedStatistics", get_statistics_by_group)
query.set_field("listDamnationesMemoriae", list_damnationes_memoriae_resolver)
query.set_field("getUserDashboard", user_dashboard_resolver)
query.set_field("getOrCreateCode", get_or_create_code_resolver)
query.set_field("listWalks", list_walks_resolver)
query.set_field("getWalk", get_walk_resolver)   
query.set_field("listWalkRatings", list_walk_ratings_resolver)
query.set_field("getWalkRating", get_walk_rating_resolver)
query.set_field("getCure", get_cure_resolver)
query.set_field("listCures", list_cures_resolver)
query.set_field("getShelter", get_shelter_resolver)
query.set_field("listShelters", list_shelters_resolver)
query.set_field("getShelterRole", get_shelter_role_resolver)
query.set_field("listShelterRoles", list_shelter_roles_resolver)
query.set_field("getShelterPet", get_shelter_pet_resolver)
query.set_field("listShelterPets", list_shelter_pets_resolver)
query.set_field("getShelterTask", get_shelter_task_resolver)
query.set_field("listShelterTasks", list_shelter_tasks_resolver)
query.set_field("getShelterWalk", get_shelter_walk_resolver)
query.set_field("listShelterWalks", list_shelter_walks_resolver)
query.set_field("listPetsNeedingWalk", list_pets_needing_walk_resolver)
query.set_field("getShelterMap", get_shelter_map_resolver)
query.set_field("listShelterMaps", list_shelter_maps_resolver)
query.set_field("getShelterBox", get_shelter_box_resolver)
query.set_field("listShelterBoxes", list_shelter_boxes_resolver)
query.set_field("listShelterBoxOccupancies", list_shelter_box_occupancies_resolver)
query.set_field("getCurrentBoxForPet", get_current_box_for_pet_resolver)
query.set_field("getShelterArea", get_shelter_area_resolver)
query.set_field("listShelterAreas", list_shelter_areas_resolver)
query.set_field("getShelterInventoryItem", get_shelter_inventory_item_resolver)
query.set_field("listShelterInventoryItems", list_shelter_inventory_items_resolver)
query.set_field("listShelterInventoryMovements", list_shelter_inventory_movements_resolver)
query.set_field("listLowStockItems", list_low_stock_items_resolver)
query.set_field("getShelterMapElement", get_shelter_map_element_resolver)
query.set_field("listShelterMapElements", list_shelter_map_elements_resolver)
query.set_field("getShelterOperationalDashboard", get_shelter_operational_dashboard_resolver)


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
mutation.set_field('linkPetToMe', link_pet_to_me_resolver)
mutation.set_field('linkPetToUser', link_pet_to_user_resolver)
mutation.set_field('addPetToUser', add_pet_to_user_resolver)
mutation.set_field('addPetToMe', add_pet_to_me_resolver)
mutation.set_field('updateOwnership', update_ownership_resolver)
mutation.set_field("refreshToken", refresh_token_resolver)
mutation.set_field("updateHealthCard", update_health_card_resolver)
mutation.set_field("createHealthCard", create_health_card_resolver)
mutation.set_field("createTreatment", create_treatment_resolver)
mutation.set_field("updateTreatment", update_treatment_resolver)
mutation.set_field("deleteTreatment", delete_treatment_resolver)
mutation.set_field("createReport", create_report_resolver)
mutation.set_field("updateReport", update_report_resolver)
mutation.set_field("respondToReport", respond_to_report_resolver)
mutation.set_field("updateMedia", update_media_resolver)
mutation.set_field("createMedia", create_media_resolver)
mutation.set_field("createCode", create_code_resolver)
mutation.set_field("checkCode", check_code_resolver)
mutation.set_field("restoreMemoriae", restore_memoriae_resolver)
mutation.set_field("verifyUser", verify_user_resolver)
mutation.set_field("resendCode", resend_code_resolver)
mutation.set_field("createWalk", create_walk_resolver)
mutation.set_field("updateWalk", update_walk_resolver)
mutation.set_field("deleteWalk", delete_walk_resolver)
mutation.set_field("createWalkRating", create_walk_rating_resolver)
mutation.set_field("updateWalkRating", update_walk_rating_resolver)
mutation.set_field("deleteWalkRating", delete_walk_rating_resolver)
mutation.set_field("createCure", create_cure_resolver)
mutation.set_field("updateCure", update_cure_resolver)
mutation.set_field("deleteCure", delete_cure_resolver)
mutation.set_field("createShelter", create_shelter_resolver)
mutation.set_field("updateShelter", update_shelter_resolver)
mutation.set_field("deleteShelter", delete_shelter_resolver)
mutation.set_field("createShelterRole", create_shelter_role_resolver)
mutation.set_field("updateShelterRole", update_shelter_role_resolver)
mutation.set_field("deleteShelterRole", delete_shelter_role_resolver)
mutation.set_field("createShelterPet", create_shelter_pet_resolver)
mutation.set_field("createShelterPets", create_shelter_pets_resolver)
mutation.set_field("changeShelter", change_shelter_resolver)
mutation.set_field("deleteShelterPet", delete_shelter_pet_resolver)
mutation.set_field("createShelterTask", create_shelter_task_resolver)
mutation.set_field("updateShelterTask", update_shelter_task_resolver)
mutation.set_field("completeShelterTask", complete_shelter_task_resolver)
mutation.set_field("skipShelterTask", skip_shelter_task_resolver)
mutation.set_field("deleteShelterTask", delete_shelter_task_resolver)
mutation.set_field("createShelterWalk", create_shelter_walk_resolver)
mutation.set_field("updateShelterWalk", update_shelter_walk_resolver)
mutation.set_field("startShelterWalk", start_shelter_walk_resolver)
mutation.set_field("completeShelterWalk", complete_shelter_walk_resolver)
mutation.set_field("cancelShelterWalk", cancel_shelter_walk_resolver)
mutation.set_field("deleteShelterWalk", delete_shelter_walk_resolver)
mutation.set_field("createShelterMap", create_shelter_map_resolver)
mutation.set_field("updateShelterMap", update_shelter_map_resolver)
mutation.set_field("deleteShelterMap", delete_shelter_map_resolver)
mutation.set_field("createShelterBox", create_shelter_box_resolver)
mutation.set_field("updateShelterBox", update_shelter_box_resolver)
mutation.set_field("deleteShelterBox", delete_shelter_box_resolver)
mutation.set_field("assignPetToBox", assign_pet_to_box_resolver)
mutation.set_field("releasePetFromBox", release_pet_from_box_resolver)
mutation.set_field("movePetBetweenBoxes", move_pet_between_boxes_resolver)
mutation.set_field("markBoxCleaned", mark_box_cleaned_resolver)
mutation.set_field("setBoxOutOfService", set_box_out_of_service_resolver)
mutation.set_field("createShelterArea", create_shelter_area_resolver)
mutation.set_field("updateShelterArea", update_shelter_area_resolver)
mutation.set_field("deleteShelterArea", delete_shelter_area_resolver)
mutation.set_field("saveShelterMapLayout", save_shelter_map_layout_resolver)
mutation.set_field("createShelterInventoryItem", create_shelter_inventory_item_resolver)
mutation.set_field("updateShelterInventoryItem", update_shelter_inventory_item_resolver)
mutation.set_field("deleteShelterInventoryItem", delete_shelter_inventory_item_resolver)
mutation.set_field("createShelterInventoryMovement", create_shelter_inventory_movement_resolver)
mutation.set_field("createShelterMapElement", create_shelter_map_element_resolver)
mutation.set_field("updateShelterMapElement", update_shelter_map_element_resolver)
mutation.set_field("deleteShelterMapElement", delete_shelter_map_element_resolver)

object_types = [query, mutation, user, dashboard, pet, ownership, health_card, treatment, report,walk, cure, shelter, shelter_role, shelter_pet, shelter_task, shelter_walk, shelter_map, shelter_box, shelter_box_occupancy, shelter_area, shelter_inventory_item, shelter_inventory_movement, walk_rating ]
