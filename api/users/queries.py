from ariadne import convert_kwargs_to_snake_case
import domain.users as users_domain
from api.middlewares import auth_middleware
from libs.logger import logger
from libs.utils import format_common_search

@convert_kwargs_to_snake_case
@auth_middleware
def list_users_resolver(obj, info, common_search):
    common_search= format_common_search(common_search)
    try:
        user = users_domain.get_users(common_search)
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