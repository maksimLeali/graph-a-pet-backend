from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_roles as shelter_roles_domain
from api.errors import format_error, error_pagination
from api.middlewares import auth_middleware
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_roles_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search = format_common_search(common_search)
    try:
        shelter_roles, pagination = shelter_roles_domain.get_paginated_shelter_roles(common_search)
        payload = {
            "success": True,
            "items": shelter_roles,
            "pagination": pagination,
        }
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_role_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        shelter_role = shelter_roles_domain.get_shelter_role(id)
        payload = {
            "success": True,
            "shelter_role": shelter_role,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "shelter_role": None,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload
