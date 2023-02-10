from ariadne import convert_kwargs_to_snake_case
from domain.pets import create_pet, update_pet, delete_pet
from utils import get_request_user
from utils.logger import logger, stringify
from controller.errors import format_error
from repository.users.models import UserRole
from controller.middlewares import min_role


@convert_kwargs_to_snake_case
def create_pet_resolver(obj, info, data):
    logger.controller(f"data: {stringify(data)}")
    try:
        pet = create_pet(data)
        payload = {
            "success": True,
            "pet": pet
        }
        logger.check(f"pet: {stringify(pet)}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "errors": format_error(e)
        }
    return payload

@convert_kwargs_to_snake_case
def update_pet_resolver(obj, info, id, data):
    logger.controller(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try:
        pet = update_pet(id, data)
        payload = {
            "success": True,
            "pet": pet
        }
        logger.check(f"data: {stringify(data)}")
    except Exception as e:  # todo not found
        payload = {
            "success": False,
            "errors": format_error(e)
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def delete_pet_resolver(obj, info, id):
    logger.controller(f"id{id}  remove")
    logger.check('here in api level')
    try: 
        token =  info.context.headers['authorization']
        current_user = get_request_user(token)
        memoriae_id = delete_pet(id, current_user['id'])
        payload= {
            "success": True,
            "id": memoriae_id
        }  
    except Exception as e: 
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e)
        }
    return payload