from ariadne import convert_kwargs_to_snake_case
import domain.walk_ratings as walk_ratings_domain
from utils.logger import logger, stringify
from utils import format_common_search
from api.errors import error_pagination, format_error
from api.middlewares import min_role, RoleLevel, auth_middleware


@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def list_walk_ratings_resolver(obj, info, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    try:
        common_search = format_common_search(common_search)
        walk_ratings, pagination = walk_ratings_domain.get_paginated_walk_ratings(common_search)
        payload = {
            "success": True,
            "items": walk_ratings,
            "pagination": pagination,
        }
        logger.check(f"walk_ratings found: {len(walk_ratings)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "items": [],
            "pagination": error_pagination
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_walk_rating_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        walk_rating = walk_ratings_domain.get_walk_rating(id)
        payload = {
            "success": True,
            "walk_rating": walk_rating
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "walk_rating": None,
            "error": format_error(e, info.context.headers['authorization'])
        }
    return payload
