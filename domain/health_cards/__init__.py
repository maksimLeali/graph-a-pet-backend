
import repository.health_cards as health_cards_data
import domain.pets as pets_domain
import domain.treatments as treatments_domain
from api.errors import NotFoundError
from utils.logger import logger, stringify
from math import ceil

def get_pet(obj,info):
    logger.check(f"pet_id: {obj['pet_id']}")
    return pets_domain.get_pet(obj['pet_id'])

def get_treatments(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        treatments, pagination = treatments_domain.get_paginated_treatments(common_search)
        logger.check(f"response: {stringify({'ownerships' : treatments , 'pagination': pagination}) }")
        return (treatments, pagination)
    except Exception as e : 
        logger.error(e)
        raise e

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
    logger.domain(f"data: {stringify(data)}")
    try:
        pet = pets_domain.get_pet(data['pet_id'])
        if(not pet):
            raise NotFoundError(f"no pet found with id: {data['pet_id']}")
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