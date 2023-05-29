from io import BytesIO
import random
import string
import repository.codes as codes_data
from utils.logger import logger, stringify
from domain.pets import get_pets

from math import ceil
from api.errors import BadRequest
from utils.firebase.storage import upload_image
import os
# from config import cfg
from PIL import Image, ImageDraw
import urllib.request

from werkzeug.utils import secure_filename
from utils import allowed_files


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def get_paginated_codes(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        codes = get_codes(common_search)

        return (codes, pagination)
    except Exception as e:
        logger.error(e)
        raise e

def create_code(data, current_user):
    logger.domain(f'data {stringify(data)} user: {stringify(current_user)}')
    try: 
        if data.get('code') == None :
            data['code'] = generate_random_string(10);
        code_filter = {
            "pagination":{
                "page":0,
                "page_size":20
            },
            "ordering":{
                "order_by":"created_at",
                "order_direction":"desc"
            },
            "filters" : {
                "and" : {"fixed" : { "code" : data.get("code") }}
            }}
        codes = get_codes(code_filter)
        if(len(codes)> 0) :
            raise BadRequest("code already present")
        
        if(data.get("ref_table") == 'pets'):
            pet_filters = {
            "pagination":{
                "page":0,
                "page_size":20
            },
            "ordering":{
                "order_by":"created_at",
                "order_direction":"desc"
            },
            "filters" : {
                "and" : {
                    "fixed" : { 
                        "id": data.get("ref_id")
                    }, 
                    "join" : {
                        "ownerships" : {
                            "and" : { 
                                "fixed" : {
                                    "user_id" : current_user.get('id'),
                                    "custody_level" : "OWNER"
                                }
                                }
                            }
                        }
                    }
            }}
            pets = get_pets(pet_filters)
            if(len(pets) == 0):
                raise BadRequest("to create a code you have to own the pet")
            

        return codes_data.create_code({**data, "created_by": current_user.get("id") })
    except Exception as e:
        logger.error(e)
        raise e

def get_codes(common_search):
    try: 
        return codes_data.get_codes(common_search)
    except Exception as e:
        logger.error(e)
        raise e
    
def get_code(id): 
    return codes_data.get_code(id)

def get_filtered_codes(filters):
    return codes_data.get_filtered_codes(filters)

def get_pagination(common_search):
    try: 
        total_items = codes_data.get_total_items(common_search)
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
    
def code_validation(code): 
    logger.domain(f'checking if code :{code} id valid')
    try: 
        code_filter = {
            "pagination":{
                "page":0,
                "page_size":20
            },
            "ordering":{
                "order_by":"created_at",
                "order_direction":"desc"
            },
            "filters" : {
                "and" : {"fixed" : { "code" : code }}
            }}
        codes = get_codes(code_filter)
        codes_length = len(codes)
        return len(codes) == 1, codes[0] if codes_length == 1 else None
    except Exception as e:
        logger.error(e)
        raise e
    
def get_or_create(ref_id, ref_table, code, current_user ):
    logger.domain(f'check if code already exist for {ref_id} of {ref_table}')
    try: 
        filters = {
            "pagination" : {"page" : 0, "page_size" : 20},
            "ordering":{
                "order_by":"created_at",
                "order_direction":"desc"
            },
            "filters" : {
                "and" : {
                    "fixed" : {
                        "ref_id" : ref_id,
                        "ref_table": ref_table
                    }
                }
            }
        }
        codes= get_codes(filters)
        if(len(codes)> 0) :
            return codes[0]
        return create_code( {"ref_id" : ref_id,
                        "ref_table": ref_table,
                        "code": code }, current_user)
    except Exception as e:
        logger.error(e)
        raise e