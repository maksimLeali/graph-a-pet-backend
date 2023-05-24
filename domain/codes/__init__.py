from io import BytesIO
import repository.codes as codes_data
from utils.logger import logger, stringify

from math import ceil
from api.errors import BadRequest
from utils.firebase.storage import upload_image
import os
# from config import cfg
from PIL import Image, ImageDraw
import urllib.request

from werkzeug.utils import secure_filename
from utils import allowed_files


def get_paginated_codes(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        codes = get_codes(common_search)

        return (codes, pagination)
    except Exception as e:
        logger.error(e)
        raise e

def create_code(data):
    logger.domain(f'data {stringify(data)}')
    try: 
        return codes_data.create_code(data)
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