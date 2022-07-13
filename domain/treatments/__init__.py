from ariadne import convert_kwargs_to_snake_case
import data.treatments as treatments_data
import domain.health_cards as health_cards_domain
from libs.logger import logger, stringify
from libs.utils import format_common_search
from math import ceil
import pydash as py_

def get_health_card(health_card_id):
    try:
        return health_cards_domain.get_health_card(health_card_id)
    except Exception as e:
        logger.error(e)
        raise e
    
def get_paginated_treatments(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:  
        pagination = get_pagination(common_search)
        treatments = get_treatments(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (treatments, pagination)
    except Exception as e:
        logger.error(e)
        raise e

def create_treatment(data):
    logger.domain(f"treatment: {stringify(data)}")
    try:
        if(data['booster']):
            booster = create_treatment(data['booster'])
            data['booster_id'] = booster.id
        treatment =  treatments_data.create_treatment(data, py_.omit('booster'))
        logger.check(f"Treatment : {stringify(data)}")
        return treatment
    except Exception as e:
        logger.error(e)
        raise e

def update_treatment(id, data):
    logger.domain(
        f"id: {id}\n"\
        f"data: {data}"
    )
    try:
        treatment= treatments_data.update_treatment(id, data)
        logger.check(f"treatment {stringify(treatment)}")
        return treatment
    except Exception as e:
        logger.error(e)
        raise e

def get_treatments(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        treatments= treatments_data.get_treatments(common_search)
        logger.check(f"treatments: {len(treatments)}")
        return treatments
    except Exception as e:
        logger.error(e)
        raise e


def get_treatment(id): 
    logger.domain(f"id: {id}")
    try:
        return treatments_data.get_treatment(id)
    except Exception as e: 
        logger.error(e)
        raise e
    
def get_pagination(common_search):
    try: 
        total_items = treatments_data.get_total_items(common_search)
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