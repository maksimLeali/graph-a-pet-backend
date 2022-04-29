from ariadne import convert_kwargs_to_snake_case
from data.models import User
def list_users_resolver(obj, info):
    try:
        user = [user.to_dict() for user in User.query.all()]
        
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
        user = User.query.get(id)
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