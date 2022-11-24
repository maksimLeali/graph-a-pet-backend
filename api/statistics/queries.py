from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.statistics as statistics_domain
from data.users.models import UserRole
from api.errors import ForbiddenError, format_error, error_pagination
from api.middlewares import auth_middleware, min_role
from libs.logger import logger, stringify
from libs.utils import format_common_search, get_request_statistic

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def list_statistics_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search= format_common_search(common_search)
    try:
        statistics, pagination = statistics_domain.get_paginated_statistics(common_search)
        logger.check(f"pafination: {stringify(pagination)}")
        payload = {
            "success": True,
            "items": statistics,
            "pagination": pagination
        }
    except Exception as e:
        logger.error(e)
        error= format_error(e,info.context.headers['authorization'])
        
        raise GraphQLError(error.get('message') , extensions=error )
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def get_statistic_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        statistic = statistics_domain.get_statistic(id)
        payload = {
            "success": True,
            "statistic": statistic
        }
        logger.check(f"statistic: {stringify(statistic)}")
    except Exception as e:  # todo not found
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "statistic": None
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def me_resolver(obj, info):
    logger.api("me")
    try:
        token =  info.context.headers['authorization']
        current_statistic = get_request_statistic(token)
        statistic = statistics_domain.get_statistic(current_statistic.get("id"))
        payload = {
            "success": True,
            "statistic": statistic,
        }
        logger.check(f"me: {statistic}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, token),
            "statistic": None
        }
    return payload
