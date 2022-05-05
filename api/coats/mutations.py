from ariadne import convert_kwargs_to_snake_case
from domain.coats import update_coat


@convert_kwargs_to_snake_case
def update_coat_resolver(obj, info, id, data):
    try:
        coat = update_coat(id, data)
        payload = {
            "success": True,
            "coat": coat
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload
