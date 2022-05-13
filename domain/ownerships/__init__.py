import data.ownerships as ownerships_data
import domain.users as users_domain
import domain.pets as pets_domain
from libs.logger import logger
from math import ceil

def get_pet(obj,info):
    return pets_domain.get_pet(obj['pet_id'])

def get_user(obj, info):
    return users_domain.get_user(obj['user_id'])

def get_paginated_ownerships(common_search):
    logger.warning(f"get ownerships pagination")
    pagination = get_pagination(common_search)
    logger.warning(f"Fetching ownerships")
    ownerships = get_ownerships(common_search)

    return (ownerships, pagination)


def create_ownership(data):
    return ownerships_data.create_ownership(data)

def update_ownership(id, data):
    return ownerships_data.update_ownership(id, data)

def get_ownerships(common_search):
    return ownerships_data.get_ownerships(common_search)

def get_ownership(id): 
    return ownerships_data.get_ownership(id)

def get_filtered_ownerships(filters):
    return ownerships_data.get_filtered_ownerships(filters)

def get_pagination(common_search):
    try: 
        total_items = ownerships_data.get_total_items(common_search)
        logger.info(total_items)
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