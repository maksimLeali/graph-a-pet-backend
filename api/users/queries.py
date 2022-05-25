from ariadne import convert_kwargs_to_snake_case
import domain.users as users_domain
from data.users.models import UserRole
from api.middlewares import auth_middleware, min_role
from libs.logger import logger, formatPath
from libs.utils import format_common_search, get_request_user
from pathlib import Path
from inspect import currentframe

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
            "errors": [str(error)],
            "items": [],
            "pagination": {}
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def get_user_resolver(obj, info, id):
    logger.info(
        f'{formatPath(__file__, currentframe())}'\
        f"id: {id}"
    )
    try:
        user = users_domain.get_user(id)
        payload = {
            "success": True,
            "user": user
        }
        logger.check(
            'API | USERS | queries.py | get_user_resolver \n'\
            f"user: {user}"
        )
    except Exception as e:  # todo not found
        payload = {
            "success": False,
            "errors": [str(e)],
            "user": None
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def me_resolver(obj, info):
    logger.info("API | USERS | queries.py | me ")
    try:
        token =  info.context.headers['authorization']
        user = get_request_user(token)
        payload = {
            "success": True,
            "user": user,
        }
    except Exception as e:  
        logger.error(f"errors: {e}")
        payload = {
            "success": False,
            "errors": ["no user found"],
            "user": None
        }
    return payload
