from ariadne import convert_kwargs_to_snake_case
import domain.users as users_domain
from api.middlewares import auth_middleware

@convert_kwargs_to_snake_case
@auth_middleware
def list_users_resolver(obj, info, commonSearch):
    print(commonSearch)
    try:
        user = users_domain.get_users()
        payload = {
            "success": True,
            "users": user
        }
    except Exception as error:
        payload = {
            "success": False,
            "errors": [str(error)]
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def get_user_resolver(obj, info, id):
    try:
        user = users_domain.get_user(id)
        payload = {
            "success": True,
            "user": user
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["User item matching {id} not found"]
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def me_resolver(obj, info):
    return "ok"