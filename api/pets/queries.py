from ariadne import convert_kwargs_to_snake_case
import domain.pets as pets_domain
from utils.logger import logger, stringify
from utils import format_common_search, get_request_user
from api.errors import InternalError, error_pagination, format_error
from api.middlewares import auth_middleware
from api.authorization.decorators import require_permission
from domain.authorization.catalog import PlatformPermissions


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.CONTENT_MANAGE, platform=True)
def list_pets_resolver(obj, info, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    try:
        common_search = format_common_search(common_search)
        pets, pagination = pets_domain.get_paginated_pets(common_search)
        payload = {
            "success": True,
            "items": pets,
            "pagination": pagination,
        }
        logger.check(f"pets found: {len(pets)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']) ,
            "items": [],
            "pagination": error_pagination 
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def list_my_pets(obj, info, common_search): 
    logger.api(f"list user pets, {stringify(common_search)}")
    try: 
        token =  info.context.headers['authorization']
        current_user = get_request_user(token)
        common_search = format_common_search(common_search)
        pets, pagination = pets_domain.get_user_pets(current_user, common_search)
        payload = {
            "success": True,
            "items": pets,
            "pagination": pagination,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']) ,
            "items": [],
            "pagination": error_pagination 
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def get_pet_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        pet = pets_domain.get_pet(id)
        payload = {
            "success": True,
            "pet": pet
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "pet":None, 
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return payload
