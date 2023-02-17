from ariadne import convert_kwargs_to_snake_case
from utils.logger import logger, stringify
from api.errors import format_error

from domain.health_cards import update_health_card, create_health_card
from api.middlewares import min_role, RoleLevel

@convert_kwargs_to_snake_case
@min_role(RoleLevel.USER.name)
def update_health_card_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}"\
        f"data: {stringify(data)}"
    )
    try:
        health_card = update_health_card(id, data)
        payload = {
            "success": True,
            "health_card": health_card
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "health_card": None,
            "error": format_error(e,info.context.headers['authorization']) ,
        }
    return payload

@convert_kwargs_to_snake_case
@min_role(RoleLevel.USER.name)
def create_health_card_resolver(obj, info, data): 
    try: 
        health_card = create_health_card(data)
        payload = {
            "success": True,
            "health_card": health_card
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "health_card": None,
            "error": format_error(e,info.context.headers['authorization']) ,
        }
    return payload