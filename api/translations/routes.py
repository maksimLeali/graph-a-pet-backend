from flask import abort, request
from api.blueprints import translations
from api.errors import format_error
from utils.logger import logger
import domain.translations as translations_domain 

@translations.route('/', methods=["GET"])
def get_translations():
    logger.api("get translations")
    try:
        translations = translations_domain.get_translations()
        return {"data": translations}
        
    except Exception as e:
        logger.error(e)
        formatted_error = format_error(e)
        logger.info(formatted_error)
        return abort(formatted_error.get("code"), formatted_error.get("message"))
    
    
@translations.route('/update', methods=["PUT"])    
def update_translations():
    logger.api('update translations')
    try:
        data = request.get_json()
        logger.info('no ')
        translations_domain.save_translations(data)
        return {"message": "ok"}
    except Exception as e:
        logger.error(e)
        formatted_error = format_error(e)
        logger.info(formatted_error)
        return abort(formatted_error.get("code"), formatted_error.get("message"))
    
    
@translations.route('/app', methods=["GET"])
def get_app_translations():
    logger.api('get app translations')
    try: 
        translations = translations_domain.get_app_translations()
        return {"data": translations}
    except Exception as e:
        logger.error(e)
        formatted_error = format_error(e)
        logger.info(formatted_error)
        return abort(formatted_error.get("code"), formatted_error.get("message"))