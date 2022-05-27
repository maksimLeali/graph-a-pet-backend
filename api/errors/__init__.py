from libs.logger import logger
class AuthenticationError(Exception):
    extensions = {"code": "401"}

class ForbiddenError(Exception):
    extension = {"code" : "403" }

class NotFoundError(Exception):
    extension = {"code" : "404"}
    
class InternalError(Exception):
    extension ={"code": "500"}

errors_types=[AuthenticationError, ForbiddenError, NotFoundError, InternalError]

error_pagination = {
    "page": 0,
    "page_size": 0,
    "total_item": 0,
    "total_pages": 0
}

def format_error (e): 
    if not type(e) in errors_types :
        logger.critical(
            "Exception not handled properly\n"\
            f"{e}"
        )
        return InternalError(str(e))
    return e