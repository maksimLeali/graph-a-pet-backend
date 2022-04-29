from ariadne import convert_kwargs_to_snake_case
import domain.pets as pets_domain

@convert_kwargs_to_snake_case
def list_pets_resolver(obj, info):
    try:
        pet = pets_domain.get_pets()
        
        payload = {
            "success": True,
            "pets": pet
        }
    except Exception as error:
        payload = {
            "success": False,
            "errors": [str(error)]
        }
    return payload

@convert_kwargs_to_snake_case
def get_pet_resolver(obj, info, id):
    try:
        pet = pets_domain.get_pet(id)
        payload = {
            "success": True,
            "pet": pet.to_dict()
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["pet item matching {id} not found"]
        }
    return payload
