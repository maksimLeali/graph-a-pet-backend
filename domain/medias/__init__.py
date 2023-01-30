from io import BytesIO
import data.medias as medias_data
from libs.logger import logger, stringify

from math import ceil
from api.errors import BadRequest
from libs.firebase.storage import upload_image
import os
# from config import cfg
from PIL import Image, ImageDraw
import urllib.request

from werkzeug.utils import secure_filename
from libs.utils import allowed_files

def upload_media(file):
    try: 
        logger.domain('try to upload media')
        if file and allowed_files(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join('temp', filename))
            return upload_image('temp'+'/', filename)
        error = BadRequest(f"file not allowed")
        raise error
    except Exception as e: 
        logger.error(e)
        raise e

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

def get_resized_to_fit_media(id, size = { "width" : 400, "height" : 400}):
    logger.domain(f"id: {id}, size: {stringify(size)}")
    try:
        media = medias_data.get_media(id)
        logger.check(media)
        with urllib.request.urlopen(media["url"]) as url:
            img = Image.open(url)
            
        img.thumbnail((size["width"], size["height"]),Image.ANTIALIAS)
        resized =(max(img.width, size['width']), max(img.height, size['height']))
        transparent_box = Image.new("RGBA", resized, (255, 255, 255, 0))
        draw = ImageDraw.Draw(transparent_box)
        draw.rectangle([(0, 0), resized], fill=(255, 255, 255, 0))
        x = (transparent_box.width - img.width )/ 2 if transparent_box.width > img.width else 0
        y = (transparent_box.height - img.height) / 2 if transparent_box.height > img.height else 0
        
        logger.info((x,y))
        transparent_box.paste(img, (int(x), int(y)))
        img_io = BytesIO()
        transparent_box.save(img_io, "PNG", quality=100)
        img_io.seek(0)
            
        return img_io, media["type"]
    except Exception as e:
        logger.error(e)
        raise e

def get_cropped_media(id, size = { "width" : 400, "height" : 400}):
    logger.domain(f"crop ->  id: {id}, size: {stringify(size)}")
    try:
        media = medias_data.get_media(id)
        with urllib.request.urlopen(media["url"]) as url:
            img = Image.open(url)
        
        logger.info(f"width: {img.width}, height: {img.height}")  
        orig_width, orig_height = img.size
        orig_ratio = orig_width / orig_height
        
        
        max_width = min(img.width,size["width"]) 
        max_height = min(img.height, size["height"])
        max_dimension = max(max_width, max_height)
        if orig_width > orig_height:
            new_width = max_dimension
            new_height = int(max_dimension / orig_ratio)
        elif orig_width < orig_height:
            new_width = int(max_dimension * orig_ratio)
            new_height = max_dimension
        else :
            new_width = max_dimension
            new_height = int(max_dimension / orig_ratio)
            new_width = int(max_dimension * orig_ratio)
            new_height = max_dimension
        
        img_resized = img.resize((new_width, new_height))
        logger.info(f"width: {img_resized.width}, height: {img_resized.height}")
        
        left= (new_width - size['width'] ) // 2
        upper = (new_height- size['height'] ) // 2
        right = left + size['width']
        lower = upper + size['height']
        
        im_cropped = img_resized.crop((left, upper,right, lower))    
        
        img_io = BytesIO()
        im_cropped.save(img_io, "PNG", quality=100)
        img_io.seek(0)
            
        return img_io, media["type"]
    except Exception as e:
        logger.error(e)
        raise e