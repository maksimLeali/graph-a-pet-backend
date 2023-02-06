from ariadne import convert_kwargs_to_snake_case
from domain.ownerships import create_ownership, update_ownership

@convert_kwargs_to_snake_case
def update_ownership_resolver(obj, info, id, data):
    try:
        ownership = update_ownership(id, data)
        payload = {
            "success": True,
            "ownership": ownership
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload
