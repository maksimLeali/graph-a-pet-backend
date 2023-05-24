from ariadne import convert_kwargs_to_snake_case
import domain.codes as codes_domain
from utils.logger import logger
from utils import format_common_search
from api.middlewares import min_role, RoleLevel
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
