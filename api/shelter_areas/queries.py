from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_areas as shelter_areas_domain
from api.errors import format_error
from api.middlewares import auth_middleware
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_areas_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search = format_common_search(common_search)
    try:
        areas, pagination = shelter_areas_domain.get_paginated_shelter_areas(common_search)
        payload = {"success": True, "items": areas, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_area_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        area = shelter_areas_domain.get_shelter_area(id)
        payload = {"success": True, "area": area}
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "area": None,
        }
    return payload
