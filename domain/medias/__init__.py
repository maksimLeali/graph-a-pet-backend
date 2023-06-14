from io import BytesIO
import repository.medias as medias_data
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

from colorthief import ColorThief


def get_luminance(hex_color):
    color = hex_color[1:]
    hex_red = int(color[0:2], base=16)
    hex_green = int(color[2:4], base=16)
    hex_blue = int(color[4:6], base=16)
    return hex_red * 0.2126 + hex_green * 0.7152 + hex_blue * 0.0722

def upload_media(file):
    try: 
        logger.domain('try to upload media')
        if file and allowed_files(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join('temp', filename))
            ct = ColorThief('temp/'+filename)
            palette = ct.get_palette(color_count=5)
            main_colors = [("#"+f"{color[0]:02x}"+f"{color[1]:02x}"+f"{color[2]:02x}").upper() for color in palette]
            colors = [ {"color" : color, "contrast" : "#FFFFFF" if get_luminance(color) < 140 else "#000000" } for color in main_colors]
            logger.domain( "-".join([color.replace("#","") for color in main_colors]))
            logger.domain(colors)
            public_url, type, encoding, size, = upload_image('temp/', filename)
            return public_url, type, encoding, size, colors
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

# def get_resized_to_fit_media(id, size = { "width" : 400, "height" : 400}):
#     logger.domain(f"id: {id}, size: {stringify(size)}")
#     try:
#         media = medias_data.get_media(id)
#         logger.check(media)
#         with urllib.request.urlopen(media["url"]) as url:
#             img = Image.open(url)
            
#         orig_ratio = img.width / img.height
#         orig_width, orig_height = img.size
#         max_width = size["width"] if size["width"] > img.width else min(img.width, size["width"])
#         max_height =  size["height"] if size["height"] > img.height else min(img.height,size["height"])
#         new_dimension = max(max_width, max_height)
        
#         # Resize the image to fit within the box
#         if orig_width <= orig_height:
#             new_width = new_dimension
#             new_height = int(new_dimension/ orig_ratio)
#         else:
#             new_width = int(new_dimension * orig_ratio)
#             new_height = new_dimension
#         # Resize the image
#         img = img.resize((new_width, new_height), Image.ANTIALIAS)
#         transparent_box = Image.new("RGBA", (new_width, new_height), (255, 255, 255, 0))
#         x = (transparent_box.width - img.width )/ 2 if transparent_box.width > img.width else 0
#         y = (transparent_box.height - img.height) / 2 if transparent_box.height > img.height else 0
#         transparent_box.paste(img, (int(x), int(y)))
#         img_io = BytesIO()
#         transparent_box.save(img_io, "PNG", quality=100)
#         img_io.seek(0)
            
#         return img_io, media["type"]
#     except Exception as e:
#         logger.error(e)
#         raise e
def get_resized_to_fit_media(id, size = { "width" : 400, "height" : 400}, args = []):
    logger.domain(f"id: {id}, size: {stringify(size)}")
    try:
        print(args)
        media = medias_data.get_media(id)
        logger.check(media)
        with urllib.request.urlopen(media["url"]) as url:
            img = Image.open(url)
            
        orig_width, orig_height = img.size
        orig_ratio = orig_width / orig_height
        if  (size['height']* orig_ratio ) > size['width'] :
            new_width = size['width']
            new_height =  int(size['width'] / orig_ratio)
        else :
            new_width = int(size['height'] * orig_ratio)
            new_height = size['height'] 

        resized =(new_width, new_height)
        img = img.resize(resized,Image.ANTIALIAS)
        transparent_box = Image.new("RGBA", (size["width"], size["height"]), (255, 255, 255, 0))
        draw = ImageDraw.Draw(transparent_box)
        draw.rectangle([(0, 0), (size["width"], size["height"])], fill=(255, 525, 255, 0))
        x = (transparent_box.width - img.width )/ 2 if transparent_box.width > img.width else 0
        y = (transparent_box.height - img.height) / 2 if transparent_box.height > img.height else 0
        transparent_box.paste(img, (int(x), int(y)))
        img_io = BytesIO()
        transparent_box.save(img_io, "PNG", quality=100)
        img_io.seek(0)
            
        return img_io, media["type"]
    except Exception as e:
        logger.error(e)
        raise e

def get_cropped_media(id, size = { "width" : 400, "height" : 400}, args=[]):
    logger.domain(f"crop ->  id: {id}, size: {stringify(size)}")
    try:
        media = medias_data.get_media(id)
        with urllib.request.urlopen(media["url"]) as url:
            img = Image.open(url)
        
        logger.info(f"width: {img.width}, height: {img.height}")  
        orig_width, orig_height = img.size
        orig_ratio = orig_width / orig_height
   
        if  (size['height']* orig_ratio ) < size['width'] :
            new_width = size['width']
            new_height =  int(size['width'] / orig_ratio)
        else :
            new_width = int(size['height'] * orig_ratio)
            new_height = size['height'] 
        
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
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
    
def get_media_file(id, args): 
    logger.domain(f'id: {id}')
    try: 
        media = medias_data.get_media(id)
        with urllib.request.urlopen(media["url"]) as url:
            img = Image.open(url)
        
        format = args.get('format')    
        img_io = BytesIO()
        if(format != None) :
            logger.critical(f'*********** {format}')
            img = img.convert('RGB')
            img.save(img_io, 'WEBP' , quality=100)
        else : 
            img.save(img_io, 'PNG' , quality=100)
            
        
        img_io.seek(0)
        return img_io, media["type"]
    except Exception as e:
        logger.error(e)
        raise e