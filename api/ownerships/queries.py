from ariadne import convert_kwargs_to_snake_case
import domain.ownerships as ownerships_domain
from libs.logger import logger
from libs.utils import format_common_search

@convert_kwargs_to_snake_case
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
            "errors": [str(error)]
        }
    return payload

@convert_kwargs_to_snake_case
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
