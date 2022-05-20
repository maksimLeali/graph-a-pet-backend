from ariadne import convert_kwargs_to_snake_case
import domain.pets as pets_domain
from libs.logger import logger
from libs.utils import format_common_search
from api.middlewares import min_role, RoleLevel

@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def list_pets_resolver(obj, info, common_search):
    try:
        common_search= format_common_search(common_search)
        pets, pagination = pets_domain.get_paginated_pets(common_search)
        payload = {
            "success": True,
            "items": pets,
            "pagination": pagination
        }
    except Exception as error:
        payload = {
            "success": False,
            "errors": [str(error)]
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def get_pet_resolver(obj, info, id):
    try:
        logger.info(f'{id}tua madre troia')
        pet = pets_domain.get_pet(id)
        payload = {
            "success": True,
            "pet": pet
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["pet item matching {id} not found"]
        }
    return payload
