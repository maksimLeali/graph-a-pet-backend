from ariadne import convert_kwargs_to_snake_case
import domain.users as users_domain

@convert_kwargs_to_snake_case
def list_users_resolver(obj, info):
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
def get_user_resolver(obj, info, id):
    try:
        user = users_domain.get_user(id)
        payload = {
            "success": True,
            "user": user.to_dict()
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["User item matching {id} not found"]
        }
    return payload
