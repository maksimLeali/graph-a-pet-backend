
import repository.walks as walks_data
import repository.treatments as treatments_data
import domain.treatments as treatments_domain
import repository.health_cards as health_cards_data
from math import ceil
from utils.logger import logger, stringify
import domain.damnationes_memoriae as damnatio_domain
import pydash as py_

def get_treatment(obj,info):
    return treatments_domain.get_treatment(obj['treatment_id'])


def create_walk(data):
    logger.domain(f'data: {stringify(data)}')
    try:

        treatment_from_walks = {
            "name": "walks",
            "date": data.get("date"),
            "type": data.get("type"),
            "duration": data.get("duration"),
            "health_card_id": data.get("health_card_id"),
        }
        treatment = treatments_data.create_treatment(treatment_from_walks)
        logger.check(f"treatment: {stringify(treatment)}")
        data["treatment_id"] = treatment['id']
        walk = walks_data.create_walk(data)        
        return walk
    except Exception as e:
        logger.error(e)
        raise e


def update_walk(id, data):
    logger.domain(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        walk = walks_data.update_walk(id, py_.pick(data, ["distance_km", "treatment_id", "overall_rating", "leash_pulling_rating", "behavior_rating", "notes"]))

        treatment_from_walks = {                       
        }
        if(data.get("date") != None):
            treatment_from_walks["date"] = data.get("date") 
        if(data.get("duration") != None):
            treatment_from_walks["duration"] = data.get("duration")
        
        logger.check(f"walk before update treatment: {stringify(walk)}")
        treatments_data.update_treatment( walk['treatment_id'],treatment_from_walks)
        logger.check(f"walk: {stringify(walk)}")
        return walk
    except Exception as e:
        logger.error(e)
        raise e
    

def delete_walk(id, walk_id ):
    logger.domain(f"id {id} remove ")
    try: 
        walk = walks_data.get_walk(id)
        damnatio_id  =damnatio_domain.delete_row(id, 'walks', walk , walk_id)
        return damnatio_id
    except Exception as e:
        logger.error(e)
        raise e

def get_paginated_walks(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        walks = get_walks(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (walks, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_walks(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        walks = walks_data.get_walks(common_search)
        logger.output(f"walks: {len(walks)}")
        return walks
    except Exception as e:
        logger.error(e)
        raise e


def get_walk(id):
    logger.domain(f"id: {id}")
    try:
        walk = walks_data.get_walk(id)
        logger.check(f"walk: {stringify(walk)}")
        return walk
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        total_items = walks_data.get_total_items(common_search)
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

