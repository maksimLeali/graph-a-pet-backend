from ariadne import convert_kwargs_to_snake_case
from domain.shelter_pets import create_shelter_pet, create_shelter_pets, create_shelter_pets_with_data, change_shelter, delete_shelter_pet
from api.middlewares import auth_middleware, min_role
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
        shelter_pet = change_shelter(data)
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
