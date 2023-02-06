from ariadne import convert_kwargs_to_snake_case
from domain.damnationes_memoriae import restore_memoriae
from utils.logger import logger

@convert_kwargs_to_snake_case
def restore_memoriae_resolver(obj, info, id,):
    logger.controller(f"restoring {id}")
    try:
        damnatio_memoriae = restore_memoriae(id)
        payload = {
            "success": True,
            "damnatio_memoriae": damnatio_memoriae
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload