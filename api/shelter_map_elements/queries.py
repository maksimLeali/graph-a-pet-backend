from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_map_elements as elements_domain
from api.errors import format_error
from api.middlewares import auth_middleware
from api.authorization.tenant import require_tenant_common_search, MAP_SCOPE
from domain.authorization.catalog import ShelterPermissions
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_map_elements_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    try:
        require_tenant_common_search(
            info, common_search, ShelterPermissions.MAP_READ, alt_scopes=MAP_SCOPE
        )
        common_search = format_common_search(common_search)
        elements, pagination = elements_domain.get_paginated_shelter_map_elements(common_search)
        payload = {"success": True, "items": elements, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_map_element_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        element = elements_domain.get_shelter_map_element(id)
        payload = {"success": True, "element": element}
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "element": None,
        }
    return payload
