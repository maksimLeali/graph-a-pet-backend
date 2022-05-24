# mutations.py
from ariadne import convert_kwargs_to_snake_case
from domain.users import create_user, update_user, login, add_pet_to_user
from api.middlewares import auth_middleware, min_role
from data.users.models import UserRole
from libs.utils import get_request_user
from libs.logger import logger

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def create_user_resolver(obj, info, data):
    try:
        user = create_user(data)
        payload = {
            "success": True,
            "user": user
        }
    except ValueError:  # date format errors
        payload = {
            "success": False,
            "errors": [f"Incorrect date format provided. Date should be in "
                       f"the format dd-mm-yyyy"]
        }
    return payload

@convert_kwargs_to_snake_case
def signup_resolver(obj, info, data):
    try:
        user = create_user(data)
        payload = {
            "success": True,
            "user": user
        }
    except ValueError:  # date format errors
        payload = {
            "success": False,
            "errors": [f"Incorrect date format provided. Date should be in "
                       f"the format dd-mm-yyyy"]
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def update_user_resolver(obj, info, id, data):
    try:
        user = update_user(id, data)
        payload = {
            "success": True,
            "user": user
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload

@convert_kwargs_to_snake_case
def login_resolver(obj, info, email, password):
    try :
        token, user = login(email, password)
        payload = {
            "success": True,
            "token": token,
            "user": user
        }
    except Exception as e:  # todo not found
        payload = {
            "success": False,
            "errors": [e]
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def add_pet_to_user_resolver(obj, info, pet, user_id):
    try: 
        new_pet, new_ownership = add_pet_to_user(user_id, pet)
        payload= {
            "success": True,
            "data": {
                "pet" : new_pet,
                "ownership": new_ownership
            }
        }        
    except Exception:
        payload = {
            "success": False,
            "errors": [f"Incorrect date format provided. Date should be in "
                       f"the format dd-mm-yyyy"]
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def add_pet_to_me_resolver(obj, info, pet):
    try: 
        token =  info.context.headers['authorization']
        user = get_request_user(token)
        new_pet, new_ownership = add_pet_to_user(user['id'], pet)
        payload= {
            "success": True,
            "data": {
                "pet" : new_pet,
                "ownership": new_ownership
            }
        }        
    except Exception:
        payload = {
            "success": False,
            "errors": [f"Incorrect date format provided. Date should be in "
                       f"the format dd-mm-yyyy"]
        }
    return payload

