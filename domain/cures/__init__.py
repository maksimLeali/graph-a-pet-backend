
import repository.cures as cures_data
import repository.treatments as treatments_data
import domain.treatments as treatments_domain
import repository.health_cards as health_cards_data
from math import ceil
from utils.logger import logger, stringify
import domain.damnationes_memoriae as damnatio_domain
import pydash as py_

def get_treatment(obj,info):
    return treatments_domain.get_treatment(obj['treatment_id'])


def create_cure(data):
    logger.domain(f'data: {stringify(data)}')
    try:

        treatment_from_cures = {
            "name": "cures",
            "date": data.get("date"),
            "type": data.get("type"),
            "duration": data.get("duration"),
            "health_card_id": data.get("health_card_id"),
        }
        treatment = treatments_data.create_treatment(treatment_from_cures)
        logger.check(f"treatment: {stringify(treatment)}")
        data["treatment_id"] = treatment['id']
        cure = cures_data.create_cure(data)        
        return cure
    except Exception as e:
        logger.error(e)
        raise e


def update_cure(id, data):
    logger.domain(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        cure = cures_data.update_cure(id, py_.pick(data, ["treatment_id", "frequency_value", "frequency_unit", "frequency_times"]))

        treatment_from_cures = {                       
        }
        if(data.get("date") != None):
            treatment_from_cures["date"] = data.get("date") 
        if(data.get("duration") != None):
            treatment_from_cures["duration"] = data.get("duration")
        
        logger.check(f"cure before update treatment: {stringify(cure)}")
        treatments_data.update_treatment( cure['treatment_id'],treatment_from_cures)
        logger.check(f"cure: {stringify(cure)}")
        return cure
    except Exception as e:
        logger.error(e)
        raise e
    

def delete_cure(id, cure_id ):
    logger.domain(f"id {id} remove ")
    try: 
        cure = cures_data.get_cure(id)
        damnatio_id  =damnatio_domain.delete_row(id, 'cures', cure , cure_id)
        return damnatio_id
    except Exception as e:
        logger.error(e)
        raise e

def get_paginated_cures(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        cures = get_cures(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (cures, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_cures(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        cures = cures_data.get_cures(common_search)
        logger.output(f"cures: {len(cures)}")
        return cures
    except Exception as e:
        logger.error(e)
        raise e


def get_cure(id):
    logger.domain(f"id: {id}")
    try:
        cure = cures_data.get_cure(id)
        logger.check(f"cure: {stringify(cure)}")
        return cure
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        total_items = cures_data.get_total_items(common_search)
        page_size = common_search['pagination']['page_size']
        total_pages = ceil(total_items / page_size)
        current_page = common_search['pagination']['page']
        pagination = {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size
        }
        logger.output(f"pagination: {stringify(pagination)}")
        return pagination
    except Exception as e:
        logger.error(e)
        raise e

