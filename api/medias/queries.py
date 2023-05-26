from ariadne import convert_kwargs_to_snake_case
import domain.medias as medias_domain
from utils.logger import logger
from utils import format_common_search
from api.middlewares import min_role, RoleLevel
from api.errors import format_error, error_pagination


@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def list_medias_resolver(obj, info, common_search):
    try:
        common_search= format_common_search(common_search)
        medias, pagination = medias_domain.get_paginated_medias(common_search)
        payload = {
            "success": True,
            "items": medias,
            "pagination": pagination
        }
    except Exception as error:
        logger.error(error)
        payload = {
            "success": False,
            "items": [],
            "pagination": error_pagination,
            "error": format_error(error)
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def get_media_resolver(obj, info, id):
    try:
        media = medias_domain.get_media(id)
        payload = {
            "success": True,
            "media": media
        }
    except Exception as error:  
        logger.error(error)# todo not found
        payload = {
            "success": False,
            "error": format_error(error)
        }
    return payload
