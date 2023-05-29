from ariadne import convert_kwargs_to_snake_case
import domain.codes as codes_domain
from utils.logger import logger
from utils import format_common_search, get_request_user

from api.middlewares import min_role, RoleLevel, auth_middleware
from api.errors import format_error, error_pagination


@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def list_codes_resolver(obj, info, common_search):
    try:
        common_search= format_common_search(common_search)
        codes, pagination = codes_domain.get_paginated_codes(common_search)
        payload = {
            "success": True,
            "items": codes,
            "pagination": pagination
        }
    except Exception as error:
        payload = {
            "success": False,
            "items": [],
            "pagination": error_pagination,
            "error": format_error(error)
        }
    return payload

@convert_kwargs_to_snake_case
def get_code_resolver(obj, info, id):
    try:
        code = codes_domain.get_code(id)
        payload = {
            "success": True,
            "code": code
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["code item matching {id} not found"]
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def get_or_create_code_resolver(obj, info, ref_id, ref_table, code): 
    logger.api(f'get code for {ref_id} of{ref_table}')
    try :
        token =  info.context.headers['authorization']
        current_user = get_request_user(token)
        code = codes_domain.get_or_create(ref_id, ref_table, code, current_user)
        payload = {
            "success": True,
            "code": code
        }
    except Exception as error:
        logger.error(error)
        payload = {
            "success": False,
            "error": format_error(error)
        } 
    return payload