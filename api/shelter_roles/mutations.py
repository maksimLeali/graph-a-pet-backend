from ariadne import convert_kwargs_to_snake_case
from domain.shelter_roles import create_shelter_role, update_shelter_role, delete_shelter_role
from api.middlewares import auth_middleware, min_role
from api.errors import format_error
from repository.users.models import UserRole
from utils.logger import logger, stringify
from utils import get_request_user


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_role_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        shelter_role = create_shelter_role(data)
        payload = {
            "success": True,
            "shelter_role": shelter_role,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def update_shelter_role_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        shelter_role = update_shelter_role(id, data)
        payload = {
            "success": True,
            "shelter_role": shelter_role,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "shelter_role": None,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def delete_shelter_role_resolver(obj, info, id):
    logger.api(f"id {id} remove")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        memoriae_id = delete_shelter_role(id, current_user['id'])
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
