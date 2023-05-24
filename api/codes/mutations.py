from ariadne import convert_kwargs_to_snake_case
from domain.codes import create_code


@convert_kwargs_to_snake_case
def create_code_resolver(obj, info, data):
    try:
        code = create_code( data)
        payload = {
            "success": True,
            "code": code
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload
