from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_maps as shelter_maps_domain
from api.errors import format_error
from api.middlewares import auth_middleware
from api.authorization.tenant import require_tenant_common_search
from domain.authorization.catalog import ShelterPermissions
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_maps_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    try:
        require_tenant_common_search(
            info, common_search, ShelterPermissions.MAP_READ
        )
        common_search = format_common_search(common_search)
        maps, pagination = shelter_maps_domain.get_paginated_shelter_maps(common_search)
        payload = {"success": True, "items": maps, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_map_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        shelter_map = shelter_maps_domain.get_shelter_map(id)
        payload = {"success": True, "map": shelter_map}
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "map": None,
        }
    return payload
