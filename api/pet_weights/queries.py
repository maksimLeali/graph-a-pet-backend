from ariadne import convert_kwargs_to_snake_case
import domain.pet_weights as pet_weights_domain
from api.middlewares import auth_middleware
from api.errors import format_error
from utils.logger import logger


@convert_kwargs_to_snake_case
@auth_middleware
def get_latest_pet_weight_resolver(obj, info, pet_id):
    logger.api(f"pet_id: {pet_id}")
    try:
        weight = pet_weights_domain.get_latest_weight(pet_id)
        return {"success": True, "weight": weight}
    except Exception as e:
        logger.error(e)
        return {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }


@convert_kwargs_to_snake_case
@auth_middleware
def get_pet_weight_stats_resolver(obj, info, pet_id, period):
    logger.api(f"pet_id: {pet_id} period: {period}")
    try:
        chart = pet_weights_domain.get_pet_weight_stats(pet_id, period)
        return {"success": True, "chart": chart}
    except Exception as e:
        logger.error(e)
        return {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
