from ariadne import convert_kwargs_to_snake_case
from api.errors import format_error
from domain.pet_bodies import update_pet_body
from utils.logger import logger , stringify

@convert_kwargs_to_snake_case
def update_pet_body_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"\
        f"data: {stringify(data)}\n"\
        )
    try:
        pet_body = update_pet_body(id, data)
        payload = {
            "success": True,
            "pet_body": pet_body
        }
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization'])
        }
    return payload
