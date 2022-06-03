import jwt
from time import time

from libs.utils import get_request_user
from libs.logger import logger
from config import cfg
import pydash as py_


def refresh_token(token):
    logger.domain(f"token:  {token}")
    request_user = get_request_user(token)
    refreshed_token = jwt.encode(
        {
            "user": py_.omit(request_user, 'password'),
            "iat": int(time()),
            "exp": int(time()) + 7 * 24*60*60
        },
        cfg['jwt']['secret'], algorithm="HS256")
    logger.check(f"Token sucessfully refreshed {refreshed_token}")
    return refreshed_token
