from libs.logger import logger
from libs.telegram import send_message_to_admin
from libs.utils import get_request_user
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

def format_error (e, token="Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjp7ImlkIjoiZWViMDJmMjctYTZkYi00ZDM5LWI0MWEtYzc3OTU2MDc4ZmIzIiwiZmlyc3RfbmFtZSI6IkFub25pbW8iLCJsYXN0X25hbWUiOiJBbm9uaW1vIiwiZW1haWwiOiJhbm9uQGFub24uY29tIiwicm9sZSI6IlVTRVIiLCJjcmVhdGVkX2F0IjoiMjAyMi0wNS0wNSAwMDowMDowMCJ9LCJpYXQiOjk5NTMzODQ0MzksImV4cCI6MTY1Mzk4OTIzOX0.0BsuDTn18kJo_bwpGNSvxo9W3L1szyGmHmvr77Pv-2o"): 
    if not type(e) in errors_types :
        logger.critical(
            "Exception not handled properly\n"\
            f"{e}"
        )
        user= get_request_user(token)
        logger.warning('sending error to admin via TELEGRAM')
        send_message_to_admin(f"utente: {user['email']} {user['first_name']} {user['last_name']}\ngenerated the following untracked error:\n🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫\n{str(e)}\n🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫")
        e= InternalError(str(e))
    return { "message" : str(e), "code": e.extension['code']}