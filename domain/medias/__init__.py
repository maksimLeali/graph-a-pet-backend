import data.medias as medias_data
import domain.users as users_domain
import domain.pets as pets_domain
from api.errors import InternalError
from libs.logger import logger, stringify
from math import ceil

def get_paginated_medias(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        medias = get_medias(common_search)

        return (medias, pagination)
    except Exception as e:
        logger.error(e)
        raise e

def create_media(data):
    logger.domain(f'data {stringify(data)}')
    try: 
        return medias_data.create_media(data)
    except Exception as e:
        logger.error(e)
        raise e
    
def update_media(id, data):
    logger.domain(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try: 
        media= medias_data.update_media(id, data)
        logger.check(f'media: {media}')
        return media
    except Exception as e: 
        logger.error(e)
        raise e

def get_medias(common_search):
    try: 
        return medias_data.get_medias(common_search)
    except Exception as e:
        logger.error(e)
        raise e
    
def get_media(id): 
    return medias_data.get_media(id)

def get_filtered_medias(filters):
    return medias_data.get_filtered_medias(filters)

def get_pagination(common_search):
    try: 
        total_items = medias_data.get_total_items(common_search)
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