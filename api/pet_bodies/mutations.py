from ariadne import convert_kwargs_to_snake_case
from domain.pet_bodies import update_pet_body


@convert_kwargs_to_snake_case
def update_pet_body_resolver(obj, info, id, data):
    try:
        pet_body = update_pet_body(id, data)
        payload = {
            "success": True,
            "pet_body": pet_body
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload
