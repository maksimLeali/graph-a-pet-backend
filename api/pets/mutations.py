from ariadne import convert_kwargs_to_snake_case
from domain.pets import create_pet, update_pet
from libs.logger import logger, stringify
from api.errors import format_error


@convert_kwargs_to_snake_case
def create_pet_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        pet = create_pet(data)
        payload = {
            "success": True,
            "pet": pet
        }
        logger.check(f"pet: {stringify(pet)}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "errors": format_error(e)
        }
    return payload

@convert_kwargs_to_snake_case
def update_pet_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try:
        pet = update_pet(id, data)
        payload = {
            "success": True,
            "pet": pet
        }
        logger.check(f"data: {stringify(data)}")
    except Exception as e:  # todo not found
        payload = {
            "success": False,
            "errors": format_error(e)
        }
    return payload
