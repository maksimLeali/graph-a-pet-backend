from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_zones as shelter_zones_domain
from api.errors import format_error
from api.middlewares import auth_middleware
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_zones_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search = format_common_search(common_search)
    try:
        zones, pagination = shelter_zones_domain.get_paginated_shelter_zones(common_search)
        payload = {"success": True, "items": zones, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_zone_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        zone = shelter_zones_domain.get_shelter_zone(id)
        payload = {"success": True, "zone": zone}
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "zone": None,
        }
    return payload
