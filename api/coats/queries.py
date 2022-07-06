from ariadne import convert_kwargs_to_snake_case
import domain.coats as coats_domain

@convert_kwargs_to_snake_case
def list_coats_resolver(obj, info):
    try:
        coats = coats_domain.get_coats()
        
        payload = {
            "success": True,
            "coats": coats
        }
    except Exception as error:
        payload = {
            "success": False,
            "errors": [str(error)]
        }
    return payload

@convert_kwargs_to_snake_case
def get_coat_resolver(obj, info, id):
    try:
        coat = coats_domain.get_coat(id)
        payload = {
            "success": True,
            "coat": coat.to_dict()
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["coat item matching {id} not found"]
        }
    return payload
