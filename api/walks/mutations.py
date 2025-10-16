# mutations.py

from ariadne import convert_kwargs_to_snake_case
from domain.walks import create_walk, update_walk, delete_walk
from api.middlewares import auth_middleware
from api.errors import format_error
from repository.users.models import UserRole
from utils.logger import logger, stringify
from utils import get_request_user


@convert_kwargs_to_snake_case
@auth_middleware
def create_walk_resolver(obj, info, data):
    logger.api(f"data {stringify(data)}")
    try:
        walk = create_walk(data)
        payload = {
            "success": True,
            "walk": walk
        }
    except Exception as e:
        logger.error(e)  # date format errors
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def update_walk_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try:
        walk = update_walk(id, data)
        payload = {
            "success": True,
            "walk": walk
        }
        logger.check(f'walk: {stringify(walk)}')
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "walk": None,
            "error": format_error(e, info.context.headers['authorization']) 
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def delete_walk_resolver(obj, info, id):
    logger.api(f"id{id}  remove")
    try: 
        token =  info.context.headers['authorization']
        current_walk = get_request_user(token)
        memoriae_id =delete_walk(id, current_walk['id'])
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
