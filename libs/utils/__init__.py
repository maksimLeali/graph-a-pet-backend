import re
import pydash as py_
import jwt
from config import cfg
from libs.logger import logger

def camel_to_snake(text: str) -> str:
    text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', text).lower()


def format_filters(to_format):
    filters = {}
    for filter in to_format:
        filters[filter['key']] = filter['value']
    return filters

def format_join(to_format):
    join={}
    for entity in to_format : 
        key= entity['key']
        join[key]= {}
        filter_keys = py_.keys(entity['value'])
        for f_key in filter_keys:
            if f_key!="join": 
                join[key][f_key]= format_filters(to_format=entity['value'][f_key])
            else:
                join[key][f_key]= format_join(to_format=entity['value'][f_key])
    return join

def format_common_search(common_search):
    return {
        "pagination": {"page": common_search['page'],
                       "page_size": common_search['page_size']},
        "ordering": {
            "order_by": common_search['order_by'],
            "order_direction": common_search['order_direction']
        },
        "filters": {
            "fixeds": format_filters(common_search['filters']['fixeds']),
            "lists": format_filters(common_search['filters']['lists']),
            "ranges": format_filters(common_search['filters']['ranges']),
            "join": format_join(common_search['filters']['join'])
        },
        "search": common_search['search'],
        "search_fields": common_search['search_fields']
    }

def get_request_user(token : str):
    logger.info(token)
    bearer = token.split('Bearer ')[1]
    decoded_bearer= jwt.decode(bearer,cfg['jwt']['secret'],algorithms=["HS256"] )
    return decoded_bearer['user']