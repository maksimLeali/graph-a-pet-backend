from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.damnationes_memoriae as damnationes_memoriae_domain
from repository.users.models import UserRole
from api.errors import ForbiddenError, format_error, error_pagination
from api.middlewares import auth_middleware, min_role
from utils.logger import logger, stringify
from utils import format_common_search

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def list_damnationes_memoriae_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
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
def get_damnatio_memoriae_resolver(obj, info, id):
    logger.api(f"id: {id}")
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