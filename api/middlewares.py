from enum import Enum
from functools import wraps
from domain.users import get_user
from time import time
from libs.logger import logger
from data.users.models import UserRole
from config import cfg 
import jwt

class RoleLevel(Enum):
    ADMIN = UserRole.ADMIN.name,
    USER = UserRole.USER.name
    

def auth_middleware(f):
    def function_wrapper(obj, info, **args):
        try :
            bearer = info.context.headers['authorization'].split('Bearer ')[1]
            logger.info(bearer)
            decoded_bearer= jwt.decode(bearer,cfg['jwt']['secret'],algorithms=["HS256"] )
            get_user(decoded_bearer['user']['id'])
        except jwt.ExpiredSignatureError as e : 
                raise Exception("Token expired")
        except :
            raise Exception('unauthorized')      
            
        return f(obj, info, **args)
    return function_wrapper

def min_role(role: UserRole):
    def decorate(fn):
        @wraps(fn)
        def wrapper(obj, info ,**args):
            
            level = { UserRole.ADMIN.name : 3, UserRole.USER.name: 2}
            try :
                bearer = info.context.headers['authorization'].split('Bearer ')[1]
                decoded_bearer= jwt.decode(bearer,cfg['jwt']['secret'],algorithms=["HS256"] )
                user = get_user(decoded_bearer['user']['id'])
            except jwt.ExpiredSignatureError as e : 
                raise Exception("Token expired")
            except Exception as e:
                raise Exception('unauthorized')      
            if level[user['role']] < level[role] :
                logger.error(
                    'API | middleware.py | min_role \n'\
                    f"{user['id']} with role {user['role']} doesn't have access to resource"    
                )
                raise Exception('insufficent role')
            logger.info('API | middleware.py | min_role \n'\
                f"{user['id']} with role {user['role']} can access resource"    
            )
            return fn(obj, info, **args)
        return wrapper
    return decorate