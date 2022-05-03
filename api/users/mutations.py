# mutations.py
from ariadne import convert_kwargs_to_snake_case
from domain.users import create_user, update_user, login, 
import jwt
from config import cfg 


@convert_kwargs_to_snake_case
def create_user_resolver(obj, info, data):
    try:
        user = create_user(data)
        payload = {
            "success": True,
            "user": user.to_dict()
        }
    except ValueError:  # date format errors
        payload = {
            "success": False,
            "errors": [f"Incorrect date format provided. Date should be in "
                       f"the format dd-mm-yyyy"]
        }
    return payload

@convert_kwargs_to_snake_case
def update_user_resolver(obj, info, id, data):
    try:
        user = update_user(id, data)
        payload = {
            "success": True,
            "user": user.to_dict()
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload

@convert_kwargs_to_snake_case
async def login_resolver(obj, info, email, password):
    try :
        token = await login(email, password)
        payload = {
            "success": True,
            "token": token
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload

@convert_kwargs_to_snake_case
async def add_pet_to_user(obj, info, pet, user_id):
    try: 
        pet
        payload= {
            "succes": True,
            "pet": pet
        }
    except Exception:
        payload = {
            "success": False,
            "errors": [f"Incorrect date format provided. Date should be in "
                       f"the format dd-mm-yyyy"]
        }
    return payload