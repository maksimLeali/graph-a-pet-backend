from ariadne import convert_kwargs_to_snake_case
from domain.cures import create_cure, update_cure, delete_cure
from utils import get_request_user
from utils.logger import logger, stringify
from api.errors import format_error
from repository.users.models import UserRole
from api.middlewares import min_role


@convert_kwargs_to_snake_case
def create_cure_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        cure = create_cure(data)
        payload = {
            "success": True,
            "cure": cure
        }
        logger.check(f"cure: {stringify(cure)}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "errors": format_error(e, info.context.headers['authorization'])
        }
    return payload

@convert_kwargs_to_snake_case
def update_cure_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try:
        cure = update_cure(id, data)
        payload = {
            "success": True,
            "cure": cure
        }
        logger.check(f"data: {stringify(data)}")
    except Exception as e:  # todo not found
        payload = {
            "success": False,
            "errors": format_error(e, info.context.headers['authorization'])
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def delete_cure_resolver(obj, info, id):
    logger.api(f"id{id}  remove")
    logger.check('here in api level')
    try: 
        token =  info.context.headers['authorization']
        current_user = get_request_user(token)
        memoriae_id = delete_cure(id, current_user['id'])
        payload= {
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