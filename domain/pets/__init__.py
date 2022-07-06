from ariadne import convert_kwargs_to_snake_case
import data.pets as pets_data
import domain.ownerships as ownerships_domain
import domain.pet_bodies as pet_bodies_domain
from libs.logger import logger, stringify
from libs.utils import format_common_search
from math import ceil
from api.errors import InternalError
import pydash as py_

@convert_kwargs_to_snake_case
def get_ownerships(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        ownerships, pagination = ownerships_domain.get_paginated_ownerships(common_search)
        logger.check(f"response: {stringify({'ownerships' : ownerships , 'pagination': pagination}) }")
        return (ownerships, pagination)
    except Exception as e : 
        logger.error(e)
        raise e

def get_body(obj, info):
    try: 
        return pet_bodies_domain.get_pet_body(obj['body_id'])
    except Exception as e: 
        logger.error(e)
        raise e
    
    
def get_paginated_pets(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:  
        pagination = get_pagination(common_search)
        pets = get_pets(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (pets, pagination)
    except Exception as e:
        logger.error(e)
        raise e

def create_pet(data):
    try:
        body = pet_bodies_domain.create_pet_body(data['body'])
        data['body_id'] = body['id']
        return pets_data.create_pet(data)
    except Exception as e:
        logger.error(e)
        raise e

def update_pet(id, data):
    logger.domain(
        f"id: {id}\n"\
        f"data: {data}"
    )
    try:
        if(data['body'] != None):
            pet_bodies_domain.update_pet_body(data['body']['id'], py_.omit(data['body'], 'id'))
        pet= pets_data.update_pet(id, py_.omit(data, 'body'))
        logger.check(f"pet {stringify(pet)}")
        return pet
    except Exception as e:
        logger.error(e)
        raise e

def get_pets(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pets= pets_data.get_pets(common_search)
        logger.check(f"pets: {len(pets)}")
        return pets
    except Exception as e:
        logger.error(e)
        raise e


def get_pet(id): 
    logger.domain(f"id: {id}")
    try:
        return pets_data.get_pet(id)
    except Exception as e: 
        logger.error(e)
        raise e
    
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