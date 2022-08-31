import re
import pydash as py_
import jwt
from time import time
from config import cfg
from libs.logger import logger, stringify

def camel_to_snake(text: str) -> str:
    text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', text).lower()


def format_filters(to_format):
    logger.info(to_format)
    filters = {}
    for filter in to_format:
        filters[filter['key']] = filter['value']
    return filters    

def format_common_search(deep_search): 
    logger.info(f"deep_search: {stringify(deep_search)}")
    return {
        "pagination": {"page": deep_search['page'],
                       "page_size": deep_search['page_size']},
        "ordering": {
            "order_by": deep_search['order_by'],
            "order_direction": deep_search['order_direction']
        },
        "filters": format_deep_filters(deep_search.get('filters'))  if deep_search.get('filters') else {}
    }
    
def format_deep_filters(filters: dict):
    logger.info(f"filters: {stringify(filters)}")
    try: 
        keys = py_.keys(filters)
        logger.info(f"{keys}")
        keys_to_promote = py_.filter_(keys, lambda x: x not in ['and', 'or', 'not'])
    
        filters['and']  = filters.get('and') if filters.get('and') != None else {}
        for key in keys_to_promote : 
            filters['and'][key] = filters[key]
            del filters[key]
        logger.warning(f"{stringify(filters)}")
        for key in filters : 
            for deep_key in filters[key]:
                logger.warning(f"key: {key} -> deep_key: {deep_key}")
                if deep_key in ['and', 'or', 'not' ] :
                    filters[key][deep_key] = format_deep_filters(filters[key][deep_key])[deep_key]
                else:
                    if deep_key == 'search': 
                        filters[key][deep_key] = filters[key][deep_key]
                    elif deep_key == 'join' : 
                        join = {}
                        for entity in filters[key][deep_key] :
                            logger.info(entity)
                            join_key = entity['key']
                            join[join_key]= format_deep_filters(entity['value'])
                        filters[key][deep_key] = join
                    else:
                        filters[key][deep_key] = format_filters(filters[key][deep_key])
        logger.check(stringify(filters))
    except Exception as e: 
        logger.warn(e)
    return filters

def get_request_user(token : str):
    logger.info(token)
    bearer = token.split('Bearer ')[1]
    decoded_bearer= jwt.decode(bearer,cfg['jwt']['secret'],algorithms=["HS256"] )
    return decoded_bearer['user']

def allowed_files(file_name:str):
    logger.info(file_name)
    return '.' in file_name and \
           file_name.rsplit('.', 1)[1].lower() in {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}