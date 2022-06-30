from ariadne import convert_kwargs_to_snake_case
from libs.logger import logger, stringify
from api.errors import format_error, error_pagination
from libs.utils import format_common_search
import domain.health_cards as health_cards_domain

@convert_kwargs_to_snake_case
def list_health_cards_resolver(obj, info, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    try:
        common_search = format_common_search(common_search)
        health_cards, pagination = health_cards_domain.get_paginated_health_cards(common_search)
        payload = {
            "success": True,
            "items": health_cards,
            "pagination": pagination,
        }
        logger.check(f"health_cards found: {len(health_cards)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']) ,
            "items": [],
            "pagination": error_pagination 
        }
    return payload
