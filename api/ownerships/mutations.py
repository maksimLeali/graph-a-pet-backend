from ariadne import convert_kwargs_to_snake_case
from api.errors import format_error
from api.middlewares import min_role, auth_middleware
import domain.ownerships as owsershis_domain
from repository.users.models import UserRole
from utils import get_request_user
from utils.logger import logger

@convert_kwargs_to_snake_case
def update_ownership_resolver(obj, info, id, data):
    try:
        ownership = owsershis_domain.update_ownership(id, data)
        payload = {
            "success": True,
            "ownership": ownership
        }
    except Exception as e: 
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization'])
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def delete_ownership_resolver(obj, info, id):
    logger.api(f"id{id}  remove")
    try: 
        token =  info.context.headers['authorization']
        current_user = get_request_user(token)
        memoriae_id = owsershis_domain.delete_ownership(id, current_user['id'])
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


@convert_kwargs_to_snake_case
@auth_middleware
def link_pet_to_me_resolver(obj, info, pet_id, custody_level):
    logger.api(f'linking pet {pet_id} to self as {custody_level}')
    try :
        token =  info.context.headers['authorization']
        current_user = get_request_user(token)
        ownership = owsershis_domain.link_pet_to_me({"pet_id" : pet_id, "user_id": current_user.get('id'), "custody_level": custody_level})
        payload  ={
            'success': True,
            'ownership': ownership
        }
    except Exception as e : 
        logger.error(e)
        payload = {
            'success': False,
            "error" : format_error(e, info.context.headers['authorization'])
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def invite_pet_ownership_resolver(obj, info, pet_id, user_id, custody_level):
    logger.api(f'invite pet {pet_id} to user {user_id} as {custody_level}')
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        ownership = owsershis_domain.invite_pet_ownership(
            pet_id, user_id, custody_level, current_user.get('id')
        )
        payload = {'success': True, 'ownership': ownership}
    except Exception as e:
        logger.error(e)
        payload = {'success': False, "error": format_error(e, info.context.headers['authorization'])}
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def accept_pet_ownership_invite_resolver(obj, info, id):
    logger.api(f'accept pet ownership invite {id}')
    try:
        current_user = get_request_user(info.context.headers['authorization'])
        ownership = owsershis_domain.accept_pet_ownership_invite(id, current_user.get('id'))
        payload = {'success': True, 'ownership': ownership}
    except Exception as e:
        logger.error(e)
        payload = {'success': False, "error": format_error(e, info.context.headers['authorization'])}
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def reject_pet_ownership_invite_resolver(obj, info, id):
    logger.api(f'reject pet ownership invite {id}')
    try:
        current_user = get_request_user(info.context.headers['authorization'])
        ownership = owsershis_domain.reject_pet_ownership_invite(id, current_user.get('id'))
        payload = {'success': True, 'ownership': ownership}
    except Exception as e:
        logger.error(e)
        payload = {'success': False, "error": format_error(e, info.context.headers['authorization'])}
    return payload


@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def link_pet_to_user_resolver(obj, info, user_id, pet_id, custody_level):
    logger.api(f'linking pet {pet_id} to user {user_id} as {custody_level}')
    try :
        ownership = owsershis_domain.link_pet_to_user({"pet_id" : pet_id, "user_id": user_id, "custody_level": custody_level})
        payload  ={
            'success': True,
            'ownership': ownership
        }
    except Exception as e : 
        logger.error(e)
        payload = {
            'success': False,
            "error" : format_error(e, info.context.headers['authorization'])
        }
    return payload