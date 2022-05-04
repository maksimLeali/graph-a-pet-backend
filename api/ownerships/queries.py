from ariadne import convert_kwargs_to_snake_case
import domain.ownerships as ownerships_domain

@convert_kwargs_to_snake_case
def list_ownerships_resolver(obj, info):
    try:
        ownerships =ownerships_domain.get_ownerships()
        
        payload = {
            "success": True,
            "ownerships": ownerships
        }
    except Exception as error:
        payload = {
            "success": False,
            "errors": [str(error)]
        }
    return payload

@convert_kwargs_to_snake_case
def get_ownership_resolver(obj, info, id):
    try:
        ownership = ownerships_domain.get_ownership(id)
        payload = {
            "success": True,
            "ownership": ownership
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["ownership item matching {id} not found"]
        }
    return payload
