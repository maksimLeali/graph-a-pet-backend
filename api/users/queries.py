from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.users as users_domain
from repository.users.models import UserRole
from api.errors import ForbiddenError, format_error, error_pagination
from api.middlewares import auth_middleware, min_role
from utils.logger import logger, stringify
from utils import format_common_search, get_request_user

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def list_users_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search= format_common_search(common_search)
    try:
        users, pagination = users_domain.get_paginated_users(common_search)
        logger.check(f"pafination: {stringify(pagination)}")
        payload = {
            "success": True,
            "items": users,
            "pagination": pagination
        }
    except Exception as e:
        logger.error(e)
        error= format_error(e,info.context.headers['authorization'])
        
        raise GraphQLError(error.get('message') , extensions=error )
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def get_user_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        user = users_domain.get_user(id)
        payload = {
            "success": True,
            "user": user
        }
        logger.check(f"user: {stringify(user)}")
    except Exception as e:  # todo not found
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']),
            "user": None
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def me_resolver(obj, info):
    logger.api("me")
    try:
        token =  info.context.headers['authorization']
        current_user = get_request_user(token)
        user = users_domain.get_user(current_user.get("id"))
        payload = {
            "success": True,
            "user": user,
        }
        logger.check(f"me: {user}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, token),
            "user": None
        }
    return payload
