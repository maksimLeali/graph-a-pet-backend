from libs.logger import logger
class BadRequest(Exception):
    extension= {"code": "400"}

class AuthenticationError(Exception):
    extensions = {"code": "401"}

class ForbiddenError(Exception):
    extension = {"code" : "403" }

class NotFoundError(Exception):
    extension = {"code" : "404"}
    
class InternalError(Exception):
    extension ={"code": "500"}


errors_types=[AuthenticationError, ForbiddenError, NotFoundError, InternalError, BadRequest]

error_pagination = {
    "page": 0,
    "page_size": 0,
    "total_item": 0,
    "total_pages": 0
}

def format_error (e): 
    logger.warning(type(e))
    if not type(e) in errors_types :
        logger.critical(
            "Exception not handled properly\n"\
            f"{e}"
        )
        e= InternalError(str(e))
    logger.warning(type(e))
    return { "message" : str(e), "code": e.extension['code']}