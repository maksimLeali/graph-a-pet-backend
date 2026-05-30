from ariadne import convert_kwargs_to_snake_case
import domain.cures as cures_domain
from utils.logger import logger, stringify
from utils import format_common_search, get_request_user
from api.errors import InternalError, error_pagination, format_error
from api.middlewares import min_role, RoleLevel, auth_middleware


@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def list_cures_resolver(obj, info, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    try:
        common_search = format_common_search(common_search)
        cures, pagination = cures_domain.get_paginated_cures(common_search)
        payload = {
            "success": True,
            "items": cures,
            "pagination": pagination,
        }
        logger.check(f"cures found: {len(cures)}")
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
def get_cure_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        cure = cures_domain.get_cure(id)
        payload = {
            "success": True,
            "cure": cure
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "cure":None, 
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return payload
