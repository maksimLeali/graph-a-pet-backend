from ariadne import convert_kwargs_to_snake_case
from api.errors import format_error
from api.middlewares import auth_middleware
from domain.codes import create_code, code_validation
from utils import get_request_user


@convert_kwargs_to_snake_case

@auth_middleware
def create_code_resolver(obj, info, data):
    try:
        token =  info.context.headers['authorization']
        current_user = get_request_user(token)
        code = create_code( data, current_user)
        payload = {
            "success": True,
            "code": code
        }
    except Exception as error:
        payload = {
            "success": False,
            "error": format_error(error)
        }
    return payload

@auth_middleware
def check_code_resolver(obj, info, code):
    try: 
        is_valid, code_found = code_validation(code)
        payload = {
            "is_valid" : is_valid,
            "code": code_found,
            "success": True
        }
    except Exception as error :
        payload = {
            "success": False,
            "error": format_error(error)
        }
    
    return payload