from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.damnationes_memoriae as damnationes_memoriae_domain
from repository.users.models import UserRole
from controller.errors import ForbiddenError, format_error, error_pagination
from controller.middlewares import auth_middleware, min_role
from utils.logger import logger, stringify
from utils import format_common_search

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def list_damnationes_memoriae_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.controller(f"common_search: {stringify(common_search)}")
    common_search= format_common_search(common_search)
    try:
        damnationes_memoriae, pagination = damnationes_memoriae_domain.get_paginated_damnationes_memoriae(common_search)
        logger.check(f"pafination: {stringify(pagination)}")
        payload = {
            "success": True,
            "items": damnationes_memoriae,
            "pagination": pagination
        }
    except Exception as e:
        logger.error(e)
        error= format_error(e,info.context.headers['authorization'])
        
        raise GraphQLError(error.get('message') , extensions=error )
    return payload


@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def get_damnationes_memoriae_by_group(obj, info, date_from, date_to, group):
    logger.controller(f"from {date_from} to {date_to} grouped {group}")
    try:
        damnationes_memoriae = damnationes_memoriae_domain.get_damnationes_memoriae_by_group(date_from, date_to, group)
        payload= {
            "success": True,
            "damnationes_memoriae": damnationes_memoriae,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "damnationes_memoriae": None
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def get_damnatio_memoriae_resolver(obj, info, id):
    logger.controller(f"id: {id}")
    try:
        damnatio_memoriae = damnationes_memoriae_domain.get_damnatio_memoriae(id)
        payload = {
            "success": True,
            "damnatio_memoriae": damnatio_memoriae
        }
        logger.check(f"damnatio_memoriae: {stringify(damnatio_memoriae)}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "damnatio_memoriae": None
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def get_real_time_damnatio_memoriae_resolver(obj, info):
    logger.controller(f"real time damnationes_memoriae ")
    try:
        damnatio_memoriae = damnationes_memoriae_domain.get_real_time_damnatio_memoriae()
        payload = {
            "success": True,
            "damnationes_memoriae": damnatio_memoriae
        }
        logger.check(f"damnatio_memoriae: {stringify(damnatio_memoriae)}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "damnationes_memoriae": None
        }
    return payload


@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def dashboard_resolver(obj, info):
    logger.controller('dashboard')
    try: 
        dashboard = damnationes_memoriae_domain.get_today_damnationes_memoriae()
        payload = {
            "success": True,
            "dashboard": dashboard
        }
        logger.check(f"damnatio_memoriae: {stringify(dashboard)}")
        
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "damnatio_memoriae": None
        }
    return payload