# mutations.py
from ariadne import convert_kwargs_to_snake_case
from domain.users import create_user, update_user, login, add_pet_to_user
from api.middlewares import auth_middleware


@convert_kwargs_to_snake_case
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
@auth_middleware
async def add_pet_to_user_resolver(obj, info, pet, user_id):
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