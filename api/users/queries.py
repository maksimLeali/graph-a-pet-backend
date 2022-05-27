from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLResolveInfo
import domain.users as users_domain
from data.users.models import UserRole
from api.errors import format_error
from api.middlewares import auth_middleware, min_role
from libs.logger import logger, stringify
from libs.utils import format_common_search, get_request_user

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def list_users_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search= format_common_search(common_search)
    try:
        users, pagination = users_domain.get_paginated_users(common_search)
        logger.check(
            f"users: {stringify(users)}\n"\
            f"pafination: {stringify(pagination)}"
        )
        payload = {
            "success": True,
            "items": users,
            "pagination": pagination
        }
    except Exception as error:
        logger.error(error)
        payload = {
            "success": False,
            "errors": [str(error)],
            "items": [],
            "pagination": {}
        }
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
        error=format_error(e)
        logger.error(e)
        payload = {
            "success": False,
            "errors": {
                "message": str(error),
                "code": error.extension['code']
                },
            "user": None
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def me_resolver(obj, info):
    logger.api("me")
    try:
        token =  info.context.headers['authorization']
        user = get_request_user(token)
        payload = {
            "success": True,
            "user": user,
        }
        logger.check(f"me: {user}")
    except Exception as e:  
        logger.error(f"errors: {e}")
        payload = {
            "success": False,
            "errors": ["no user found"],
            "user": None
        }
    return payload
