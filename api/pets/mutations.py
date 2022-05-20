from ariadne import convert_kwargs_to_snake_case
from domain.pets import create_pet, update_pet


@convert_kwargs_to_snake_case
def create_pet_resolver(obj, info, data):
    try:
        pet = create_pet(data)
        payload = {
            "success": True,
            "pet": pet
        }
    except Exception as e:  # date format errors
        payload = {
            "success": False,
            "errors": e
        }
    return payload

@convert_kwargs_to_snake_case
def update_pet_resolver(obj, info, id, data):
    try:
        pet = update_pet(id, data)
        payload = {
            "success": True,
            "pet": pet.to_dict()
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload
