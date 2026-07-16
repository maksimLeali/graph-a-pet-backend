from ariadne import convert_kwargs_to_snake_case
import domain.shelter_pets as shelter_pets_domain
from domain.shelter_pets import create_shelter_pet, create_shelter_pets, create_shelter_pets_with_data, change_shelter, delete_shelter_pet
from api.middlewares import auth_middleware, min_role, assert_shelter_role
from api.authorization.decorators import authorize_from_token
from domain.authorization.catalog import ShelterPermissions
from api.errors import format_error
from repository.users.models import UserRole
from utils.logger import logger, stringify
from utils import get_request_user


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_pet_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        shelter_pet = create_shelter_pet(data)
        payload = {
            "success": True,
            "shelter_pet": shelter_pet,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_pets_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        shelter_pets = create_shelter_pets(data)
        payload = {
            "success": True,
            "shelter_pets": shelter_pets,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_pets_with_data_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        shelter_pets = create_shelter_pets_with_data(data)
        payload = {
            "success": True,
            "shelter_pets": shelter_pets,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def change_shelter_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        # STAFF+ required on BOTH source and destination shelters
        assert_shelter_role(token, data["shelter_id_from"], "STAFF")
        assert_shelter_role(token, data["shelter_id_to"], "STAFF")
        me = get_request_user(token)
        shelter_pet = change_shelter(data, me["id"])
        payload = {
            "success": True,
            "shelter_pet": shelter_pet,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def set_shelter_pet_published_resolver(obj, info, shelter_pet_id, is_published):
    logger.api(f"shelter_pet_id: {shelter_pet_id} is_published: {is_published}")
    try:
        sp = shelter_pets_domain.get_shelter_pet(shelter_pet_id)
        authorize_from_token(
            info.context.headers['authorization'],
            ShelterPermissions.PETS_PUBLISH,
            sp["shelter_id"],
        )
        shelter_pet = shelter_pets_domain.set_shelter_pet_published(
            shelter_pet_id, is_published
        )
        payload = {
            "success": True,
            "shelter_pet": shelter_pet,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def set_shelter_pet_assignees_resolver(obj, info, shelter_pet_id, user_ids=None, shelter_person_ids=None):
    logger.api(
        f"shelter_pet_id: {shelter_pet_id} user_ids: {stringify(user_ids)} "
        f"shelter_person_ids: {stringify(shelter_person_ids)}"
    )
    try:
        sp = shelter_pets_domain.get_shelter_pet(shelter_pet_id)
        authorize_from_token(
            info.context.headers['authorization'],
            ShelterPermissions.PETS_UPDATE,
            sp["shelter_id"],
        )
        shelter_pet = shelter_pets_domain.set_shelter_pet_assignees(
            shelter_pet_id, user_ids, shelter_person_ids
        )
        payload = {
            "success": True,
            "shelter_pet": shelter_pet,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def delete_shelter_pet_resolver(obj, info, id):
    logger.api(f"id {id} remove")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        memoriae_id = delete_shelter_pet(id, current_user['id'])
        payload = {
            "success": True,
            "id": memoriae_id,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload
