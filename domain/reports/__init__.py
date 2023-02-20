
import repository.reports as reports_data
import domain.pets as pets_domain
import domain.users as users_domain
from api.errors import NotFoundError
from utils.logger import logger, stringify
from math import ceil

def get_pet(obj,info):
    logger.check(f"pet_id: {obj['pet_id']}")
    return pets_domain.get_pet(obj['pet_id'])

def get_user(obj,info):
    logger.check(f"user_id: {obj['user_id']}")
    return users_domain.get_user(obj['user_id'])

def get_coordinates(obj, info): 
    logger.check(f"id: {obj['id']}")
    return { "latitude" : obj["latitude"], "longitude": obj["longitude"]}

def get_report(id): 
    logger.domain(f"id: {id}")
    try:
        report= reports_data.get_report(id)
        logger.check(f"report: {stringify(report)}")
        return report
    except Exception as e: 
        logger.error(e)
        raise e

def create_report(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        return reports_data.create_report(data)
    except Exception as e:
        logger.error(e)
        raise e

def update_report(id, data):
    logger.domain(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try: 
        report= reports_data.update_report(id, data)
        logger.check(f"report: {stringify(report)}")
        return report
    except Exception as e: 
        logger.error(e)
        raise e

def get_reports(common_search):
    return reports_data.get_reports(common_search)

def get_paginated_reports(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:  
        pagination = get_pagination(common_search)
        reports = get_reports(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (reports, pagination)
    except Exception as e:
        logger.error(e)
        raise e
    
def get_pagination(common_search):
    try: 
        total_items = reports_data.get_total_items(common_search)
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