import repository.ownerships as ownerships_data
import domain.users as users_domain
import domain.pets as pets_domain
from api.errors import InternalError
import domain.damnationes_memoriae as damnatio_domain
from utils.logger import logger, stringify
from math import ceil

def get_pet(obj,info):
    return pets_domain.get_pet(obj['pet_id'])

def get_user(obj, info):
    return users_domain.get_user(obj['user_id'])

def get_paginated_ownerships(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        ownerships = get_ownerships(common_search)

        return (ownerships, pagination)
    except Exception as e:
        logger.error(e)
        raise e

def create_ownership(data):
    return ownerships_data.create_ownership(data)

def update_ownership(id, data):
    logger.domain(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try: 
        ownership= ownerships_data.update_ownership(id, data)
        logger.check(f'ownership: {ownership}')
        return ownership
    except Exception as e: 
        logger.error(e)
        raise e

def get_ownerships(common_search):
    try: 
        return ownerships_data.get_ownerships(common_search)
    except Exception as e:
        logger.error(e)
        raise e
    
def get_ownership(id): 
    return ownerships_data.get_ownership(id)

def get_filtered_ownerships(filters):
    return ownerships_data.get_filtered_ownerships(filters)

def get_pagination(common_search):
    try: 
        total_items = ownerships_data.get_total_items(common_search)
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
        raise e

def delete_ownership(id, user_id ):
    logger.domain(f"id {id} remove ")
    try: 
        ownership = ownerships_data.get_ownership(id)
        logger.check(stringify(ownership))
        memoriae_id = damnatio_domain.delete_row(id, 'ownerships', ownership ,user_id)
        return memoriae_id
    except Exception as e:
        logger.error(e)
        raise e