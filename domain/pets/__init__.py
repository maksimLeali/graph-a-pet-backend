from ariadne import convert_kwargs_to_snake_case
import data.pets as pets_data
import domain.ownerships as ownerships_domain
import domain.pet_bodies as pet_bodies_domain
from libs.logger import logger
from libs.utils import format_common_search
from math import ceil

@convert_kwargs_to_snake_case
def get_ownerships(obj, info, common_search):
    common_search= format_common_search(common_search)
    common_search['filters']['fixeds']['pet_id'] = obj['id']
    ownerships, pagination = ownerships_domain.get_paginated_ownerships(common_search)
    return { "items": ownerships, "pagination": pagination}


def get_body(obj, info):
    return pet_bodies_domain.get_pet_body(obj['body_id'])

def get_paginated_pets(common_search):
    pagination = get_pagination(common_search)
    pets = get_pets(common_search)

    return (pets, pagination)

def create_pet(data):
    body = pet_bodies_domain.create_pet_body(data['body'])
    data['body_id'] = body['id']
    return pets_data.create_pet(data)

def update_pet(id, data):
    return pets_data.update_pet(id, data)

def get_pets(common_search):
    return pets_data.get_pets(common_search)

def get_pet(id): 
    return pets_data.get_pet(id)

def get_pagination(common_search):
    try: 
        total_items = pets_data.get_total_items(common_search)
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