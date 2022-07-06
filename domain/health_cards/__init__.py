
import data.health_cards as health_cards_data
from libs.logger import logger, stringify
from math import ceil


def get_health_card(id): 
    logger.domain(f"id: {id}")
    try:
        health_card= health_cards_data.get_health_card(id)
        logger.check(f"health_card: {stringify(health_card)}")
        return health_card
    except Exception as e: 
        logger.error(e)
        raise e

def create_health_card(data):
    try:
        return health_cards_data.create_health_card(data)
    except Exception as e:
        logger.error(e)
        raise e

def update_health_card(id, data):
    logger.domain(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try: 
        health_card= health_cards_data.update_health_card(id, data)
        logger.check(f"health_card: {stringify(health_card)}")
        return health_card
    except Exception as e: 
        logger.error(e)
        raise e

def get_health_cards(common_search):
    return health_cards_data.get_health_cards(common_search)

def get_paginated_health_cards(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:  
        pagination = get_pagination(common_search)
        health_cards = get_health_cards(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (health_cards, pagination)
    except Exception as e:
        logger.error(e)
        raise e
    
def get_pagination(common_search):
    try: 
        total_items = health_cards_data.get_total_items(common_search)
        page_size = common_search['pagination']['page_size']
        total_pages = ceil(total_items /page_size)
        current_page = common_search['pagination']['page']
        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(e)
        raise Exception(e)