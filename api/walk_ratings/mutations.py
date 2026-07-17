from ariadne import convert_kwargs_to_snake_case
from domain.walk_ratings import create_walk_rating, update_walk_rating, delete_walk_rating
from utils import get_request_user
from utils.logger import logger, stringify
from api.errors import format_error
from api.middlewares import auth_middleware
from api.authorization.decorators import require_permission
from domain.authorization.catalog import PlatformPermissions


@convert_kwargs_to_snake_case
@auth_middleware
def create_walk_rating_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        walk_rating = create_walk_rating(data)
        payload = {
            "success": True,
            "walk_rating": walk_rating
        }
        logger.check(f"walk_rating: {stringify(walk_rating)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization'])
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def update_walk_rating_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        walk_rating = update_walk_rating(id, data)
        payload = {
            "success": True,
            "walk_rating": walk_rating
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization'])
        }
    return payload


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.CONTENT_MANAGE, platform=True)
def delete_walk_rating_resolver(obj, info, id):
    logger.api(f"id{id}  remove")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        memoriae_id = delete_walk_rating(id, current_user['id'])
        payload = {
            "success": True,
            "id": memoriae_id
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization'])
        }
    return payload
