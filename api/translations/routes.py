from flask import abort
from api.blueprints import translations
from api.errors import format_error
from utils.logger import logger
import domain.translations as translations_domain 

@translations.route('/', methods=["GET"])
def get_translations():
    logger.api("get translations")
    try:
        
        return translations_domain.get_translations()
        
    except Exception as e:
        logger.error(e)
        formatted_error = format_error(e)
        logger.info(formatted_error)
        return abort(formatted_error.get("code"), formatted_error.get("message"))