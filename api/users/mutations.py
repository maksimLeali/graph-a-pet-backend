# mutations.py
from ariadne import convert_kwargs_to_snake_case
from domain.users import create_user, update_user, login, add_pet_to_user
from api.middlewares import auth_middleware, min_role
from api.errors import format_error
from data.users.models import UserRole
from libs.utils import get_request_user
from libs.logger import logger, stringify

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def create_user_resolver(obj, info, data):
    logger.api(f"data {stringify(data)}")
    try:
        user = create_user(data)
        payload = {
            "success": True,
            "user": user
        }
    except Exception as e:
        logger.error(e)  # date format errors
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return payload

@convert_kwargs_to_snake_case
def signup_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        user = create_user(data)
        payload = {
            "success": True,
            "user": user
        }
        logger.check(f"user: {stringify(user)}")
    except Exception as e:
        logger.error(e)  # date format errors
        payload = {
            "success": False,
            "user": None,
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def update_user_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try:
        user = update_user(id, data)
        payload = {
            "success": True,
            "user": user
        }
        logger.check(f'user: {stringify(user)}')
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "user": None,
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return payload

@convert_kwargs_to_snake_case
def login_resolver(obj, info, email, password):
    logger.api(f"email: {email}, password: {password}")
    try :
        token, user = login(email, password)
        payload = {
            "success": True,
            "token": token,
            "user": user
        }
        logger.check(f"user: {stringify(user)}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "token": None,
            "user": None,
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def add_pet_to_user_resolver(obj, info, pet, user_id, custody_level):
    logger.api(
        f"user_id: {user_id}\n"\
        f"pet: {stringify(pet)}"
    )
    try: 
        new_pet, new_ownership = add_pet_to_user(user_id, pet, custody_level)
        payload= {
            "success": True,
            "data": {
                "pet" : new_pet,
                "ownership": new_ownership
            }
        }        
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "data": None,
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def add_pet_to_me_resolver(obj, info, pet, custody_level):
    logger.api(f"pet: {stringify(pet)}")
    try: 
        token =  info.context.headers['authorization']
        user = get_request_user(token)
        new_pet, new_ownership = add_pet_to_user(user['id'], pet, custody_level)
        payload= {
            "success": True,
            "data": {
                "pet" : new_pet,
                "ownership": new_ownership
            }
        }        
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "errors": [f"Incorrect date format provided. Date should be in "
                       f"the format dd-mm-yyyy"]
        }
    return payload

