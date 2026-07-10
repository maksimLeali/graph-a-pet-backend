from ariadne import convert_kwargs_to_snake_case
import domain.pet_weights as pet_weights_domain
from api.middlewares import auth_middleware
from api.errors import format_error
from utils.logger import logger, stringify


@convert_kwargs_to_snake_case
@auth_middleware
def create_pet_weight_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        weight = pet_weights_domain.create_pet_weight(data)
        return {"success": True, "weight": weight}
    except Exception as e:
        logger.error(e)
        return {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
