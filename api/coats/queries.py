from ariadne import convert_kwargs_to_snake_case
import domain.coats as coats_domain
from utils.logger import logger
from api.errors import format_error

@convert_kwargs_to_snake_case
def list_coats_resolver(obj, info):
    logger.info('listing coats')
    try:
        coat = coats_domain.get_coats()
        logger.check(f"found {len(coat)}")
        payload = {
            "success": True,
            "coats": coat
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']) 
        }
    return payload

@convert_kwargs_to_snake_case
def get_coat_resolver(obj, info, id):
    try:
        coat = coats_domain.get_coat(id)
        payload = {
            "success": True,
            "coat": coat.to_dict()
        }
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "error":format_error(e, info.context.headers['authorization']) 
        }
    return payload
