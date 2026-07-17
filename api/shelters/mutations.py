from ariadne import convert_kwargs_to_snake_case
from domain.shelters import create_shelter, create_personal_workspace, update_shelter, delete_shelter
from api.middlewares import auth_middleware
from api.authorization.decorators import require_permission
from domain.authorization.catalog import PlatformPermissions
from api.errors import format_error
from utils.logger import logger, stringify
from utils import get_request_user


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.SHELTERS_MANAGE, platform=True)
def create_shelter_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        shelter = create_shelter(data, current_user)
        payload = {
            "success": True,
            "shelter": shelter,
        }
        logger.check(f"shelter: {stringify(shelter)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def create_personal_workspace_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        shelter = create_personal_workspace(data, current_user["id"])
        payload = {
            "success": True,
            "shelter": shelter,
        }
        logger.check(f"shelter: {stringify(shelter)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def update_shelter_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        shelter = update_shelter(id, data)
        payload = {
            "success": True,
            "shelter": shelter,
        }
        logger.check(f"shelter: {stringify(shelter)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "shelter": None,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.SHELTERS_MANAGE, platform=True)
def delete_shelter_resolver(obj, info, id):
    logger.api(f"id {id} remove")
    logger.critical(f"id {id} remove")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        logger.critical(f"current_user: {stringify(current_user)}")
        memoriae_id = delete_shelter(id, current_user['id'])
        payload = {
            "success": True,
            "id": memoriae_id,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload
