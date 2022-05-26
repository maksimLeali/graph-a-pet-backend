
class AuthenticationError(Exception):
    extensions = {"code": "401"}

class ForbiddenError(Exception):
    extension = {"code" : "403" }

class NotFoundError(Exception):
    extension = {"code" : "404"}
    
class InternalError(Exception):
    extension ={"code": "500"}

error_pagination = {
    "page": 0,
    "page_size": 0,
    "total_item": 0,
    "total_pages": 0
}