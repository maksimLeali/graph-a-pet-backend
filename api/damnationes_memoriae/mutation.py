from ariadne import convert_kwargs_to_snake_case
from domain.damnationes_memoriae import restore_memoriae
from utils import get_request_user
from utils.logger import logger
from api.errors import format_error

@convert_kwargs_to_snake_case
def restore_memoriae_resolver(obj, info, id,):
    logger.api(f"restoring {id}")
    try:
        token =  info.context.headers['authorization']
        current_user = get_request_user(token)
        restored, table = restore_memoriae(id, current_user)
        payload = {
            "success": True,
            "table": table ,
            "restored": restored
        }
    except Exception as e:  # todo not found
        logger.error(e)
        
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization'])
        }
    return payload