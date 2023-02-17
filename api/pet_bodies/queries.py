from ariadne import convert_kwargs_to_snake_case
import domain.pet_bodies as pet_bodies_domain

@convert_kwargs_to_snake_case
def list_pet_bodies_resolver(obj, info):
    try:
        pet_body = pet_bodies_domain.get_pet_bodies()
        
        payload = {
            "success": True,
            "pet_bodies": pet_body
        }
    except Exception as error:
        payload = {
            "success": False,
            "errors": [str(error)]
        }
    return payload

@convert_kwargs_to_snake_case
def get_pet_body_resolver(obj, info, id):
    try:
        pet_body = pet_bodies_domain.get_pet_body(id)
        payload = {
            "success": True,
            "pet_body": pet_body.to_dict()
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["pet_body item matching {id} not found"]
        }
    return payload
