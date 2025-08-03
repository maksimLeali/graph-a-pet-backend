from ariadne import convert_kwargs_to_snake_case
import repository.pets as pets_data
import domain.ownerships as ownerships_domain
import domain.medias as media_domain
import repository.damnationes_memoriae as damnatio
import domain.damnationes_memoriae as damnatio_domain
from utils.logger import logger, stringify
from math import ceil

import pydash as py_

@convert_kwargs_to_snake_case
def get_main_pic(pet_id: str):
    logger.domain(f"id {pet_id}")
    try:
        medias = media_domain.get_medias({"ordering": {"order_direction": "ASC", "order_by": "created_at"}, "pagination": {
                                        "page_size": 10, "page": 0}, "filters": {"and": {"fixed": {"ref_id ": pet_id, "scope": "pet_main_picture"}}}})
        media= medias[0]
        logger.check(media)
        return media
    except Exception as e:
        logger.error(e)
        raise e

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

@convert_kwargs_to_snake_case
def get_pictures(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pictures, pagination = media_domain.get_paginated_medias(common_search)

        logger.check(f"response: {stringify({'pictures' : pictures , 'pagination': pagination}) }")
        return (pictures, pagination)
    except Exception as e : 
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
    
def get_user_pets(user, common_search):
    logger.domain(f"common_search: {stringify(common_search)}")

    if 'filters' not in common_search:
        common_search['filters'] = {}

    if 'and' not in common_search['filters']:
       common_search['filters']['and'] =  {}

    if 'join' not in common_search['filters']['and']:
        common_search['filters']['and']['join'] = {}

    # Check if 'ownerships' key exists in common_search['join'], if not, initialize it as an empty dictionary
    if 'ownerships' not in common_search['filters']['and']['join']:
        common_search['filters']['and']['join']['ownerships'] = {}

    # Check if 'fixed' key exists in common_search['join']['ownerships'], if not, initialize it as an empty dictionary
    if 'and' not in common_search['filters']['and']['join']['ownerships']:
        common_search['filters']['and']['join']['ownerships']['and'] = {}

    if 'fixed' not in common_search['filters']['and']['join']['ownerships']['and']:
        common_search['filters']['and']['join']['ownerships']['and']['fixed'] = {}
        
    common_search['filters']['and']['join']['ownerships']['and']['fixed'] =  {**common_search['filters']['and']['join']['ownerships']['and']['fixed'], "user_id" : user.get("id") }
    logger.critical(stringify(common_search))
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
        pet = pets_data.get_pet(id)
        pet= pets_data.update_pet(id, data)
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

def delete_pet(id, user_id):
    logger.domain(f"id {id} remove ")
    try: 
        pet = pets_data.get_pet(id)
        damnatio_id  =damnatio_domain.delete_row(id, 'pets', pet, user_id)
        return damnatio_id
    except Exception as e:
        logger.error(e)
        raise e