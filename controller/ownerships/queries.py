from ariadne import convert_kwargs_to_snake_case
import domain.ownerships as ownerships_domain
from utils.logger import logger
from utils import format_common_search
from controller.middlewares import min_role, RoleLevel
from controller.errors import format_error, error_pagination


@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def list_ownerships_resolver(obj, info, common_search):
    try:
        common_search= format_common_search(common_search)
        ownerships, pagination = ownerships_domain.get_paginated_ownerships(common_search)
        payload = {
            "success": True,
            "items": ownerships,
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
@min_role(RoleLevel.ADMIN.name)
def get_ownership_resolver(obj, info, id):
    try:
        ownership = ownerships_domain.get_ownership(id)
        payload = {
            "success": True,
            "ownership": ownership
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["ownership item matching {id} not found"]
        }
    return payload
