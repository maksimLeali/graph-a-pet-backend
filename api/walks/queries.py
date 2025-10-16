from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.walks as walks_domain
from repository.users.models import UserRole
from api.errors import ForbiddenError, format_error, error_pagination
from api.middlewares import auth_middleware, min_role
from utils.logger import logger, stringify
from utils import format_common_search

@convert_kwargs_to_snake_case
@auth_middleware
def list_walks_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search= format_common_search(common_search)
    try:
        walks, pagination = walks_domain.get_paginated_walks(common_search)
        logger.check(f"pafination: {stringify(pagination)}")
        payload = {
            "success": True,
            "items": walks,
            "pagination": pagination
        }
    except Exception as e:
        logger.error(e)
        error= format_error(e,info.context.headers['authorization'])
        
        raise GraphQLError(error.get('message') , extensions=error )
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def get_walk_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        walk = walks_domain.get_walk(id)
        payload = {
            "success": True,
            "walk": walk
        }
        logger.check(f"walk: {stringify(walk)}")
    except Exception as e:  # todo not found
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "walk": None
        }
    return payload