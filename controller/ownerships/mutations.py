from ariadne import convert_kwargs_to_snake_case
from controller.errors import format_error
from controller.middlewares import min_role
from domain.ownerships import create_ownership, update_ownership, delete_ownership
from repository.users.models import UserRole
from utils import get_request_user
from utils.logger import logger

@convert_kwargs_to_snake_case
def update_ownership_resolver(obj, info, id, data):
    try:
        ownership = update_ownership(id, data)
        payload = {
            "success": True,
            "ownership": ownership
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def delete_ownership_resolver(obj, info, id):
    logger.controller(f"id{id}  remove")
    try: 
        token =  info.context.headers['authorization']
        current_user = get_request_user(token)
        memoriae_id = delete_ownership(id, current_user['id'])
        payload= {
            "success": True,
            "id": memoriae_id
        }  
    except Exception as e: 
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e)
        }
    return payload