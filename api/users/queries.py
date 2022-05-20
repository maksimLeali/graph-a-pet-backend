from ariadne import convert_kwargs_to_snake_case
import domain.users as users_domain
from data.users.models import UserRole
from api.middlewares import auth_middleware, min_role
from libs.logger import logger
from libs.utils import format_common_search, get_request_user

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def list_users_resolver(obj, info, common_search):
    common_search= format_common_search(common_search)
    try:
        users, pagination = users_domain.get_paginated_users(common_search)
        payload = {
            "success": True,
            "items": users,
            "pagination": pagination
        }
    except Exception as error:
        payload = {
            "success": False,
            "errors": [str(error)]
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def get_user_resolver(obj, info, id):
    try:
        user = users_domain.get_user(id)
        payload = {
            "success": True,
            "user": user
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["User item matching {id} not found"]
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def me_resolver(obj, info):
    try:
        token =  info.context.headers['authorization']
        user = get_request_user(token)
        payload = {
            "success": True,
            "user": user
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["User item matching {id} not found"]
        }
    return payload
