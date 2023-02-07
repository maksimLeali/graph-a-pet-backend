from ariadne import convert_kwargs_to_snake_case
from domain.damnationes_memoriae import restore_memoriae
from utils.logger import logger
from controller.errors import format_error

@convert_kwargs_to_snake_case
def restore_memoriae_resolver(obj, info, id,):
    logger.controller(f"restoring {id}")
    try:
        restored, table = restore_memoriae(id)
        payload = {
            "success": True,
            "table": table ,
            "restored": restored
        }
    except Exception as e:  # todo not found
        logger.error(e)
        
        payload = {
            "success": False,
            "error": format_error(e)
        }
    return payload