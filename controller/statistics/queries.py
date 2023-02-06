from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.statistics as statistics_domain
from repository.users.models import UserRole
from controller.errors import ForbiddenError, format_error, error_pagination
from controller.middlewares import auth_middleware, min_role
from utils.logger import logger, stringify
from utils import format_common_search

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def list_statistics_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.controller(f"common_search: {stringify(common_search)}")
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
def get_statistics_by_group(obj, info, date_from, date_to, group):
    logger.controller(f"from {date_from} to {date_to} grouped {group}")
    try:
        statistics = statistics_domain.get_statistics_by_group(date_from, date_to, group)
        payload= {
            "success": True,
            "statistics": statistics,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "statistics": None
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def get_statistic_resolver(obj, info, id):
    logger.controller(f"id: {id}")
    try:
        statistic = statistics_domain.get_statistic(id)
        payload = {
            "success": True,
            "statistic": statistic
        }
        logger.check(f"statistic: {stringify(statistic)}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "statistic": None
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def get_real_time_statistic_resolver(obj, info):
    logger.controller(f"real time statistics ")
    try:
        statistic = statistics_domain.get_real_time_statistic()
        payload = {
            "success": True,
            "statistics": statistic
        }
        logger.check(f"statistic: {stringify(statistic)}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "statistics": None
        }
    return payload


@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def dashboard_resolver(obj, info):
    logger.controller('dashboard')
    try: 
        dashboard = statistics_domain.get_today_statistics()
        payload = {
            "success": True,
            "dashboard": dashboard
        }
        logger.check(f"statistic: {stringify(dashboard)}")
        
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "statistic": None
        }
    return payload