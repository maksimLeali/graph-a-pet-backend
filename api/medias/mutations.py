from ariadne import convert_kwargs_to_snake_case
from domain.medias import create_media, update_media, delete_media
from utils import get_request_user
from utils.logger import logger
from api.errors import format_error
from api.authorization.decorators import require_permission
from domain.authorization.catalog import PlatformPermissions

@convert_kwargs_to_snake_case
def update_media_resolver(obj, info, id, data):
    try:
        media = update_media(id, data)
        payload = {
            "success": True,
            "media": media
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload

@convert_kwargs_to_snake_case
def create_media_resolver(obj, info, data):
    try:
        media = create_media( data)
        payload = {
            "success": True,
            "media": media
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload

@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.APP_USE, platform=True)
def delete_media_resolver(obj, info, id):
    logger.api(f"id {id} remove")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        memoriae_id = delete_media(id, current_user['id'])
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
