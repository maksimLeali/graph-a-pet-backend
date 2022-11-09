from enum import Enum
from functools import wraps
from typing import Any

from graphql import GraphQLError, GraphQLResolveInfo
from api.errors import AuthenticationError, ForbiddenError, format_error
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
    def function_wrapper(obj: Any, info: GraphQLResolveInfo, **args):
        logger.middleware("check if user is authorized")
        try :
            bearer = info.context.headers['authorization'].split('Bearer ')[1]
            decoded_bearer= jwt.decode(bearer,cfg['jwt']['secret'],algorithms=["HS256"] )
            logger.info(decoded_bearer)
            get_user(decoded_bearer['user']['id'])
        except jwt.ExpiredSignatureError as e : 
            logger.error(f"Token expired for user {decoded_bearer['user']['id']} ")
            raise Exception("Token expired")
        except Exception as e:
            logger.error(e)        
            raise AuthenticationError('unauthorized')      
            
        return f(obj, info, **args)
    return function_wrapper

def min_role(role: UserRole):
    def decorate(fn):
        @wraps(fn)
        def wrapper(obj: Any, info: GraphQLResolveInfo ,**args):
            try:
                level = { UserRole.ADMIN.name : 3, UserRole.USER.name: 2}
                logger.middleware(f"min role: {role}")
                try :
                    bearer = info.context.headers['authorization'].split('Bearer ')[1]
                    decoded_bearer= jwt.decode(bearer,cfg['jwt']['secret'],algorithms=["HS256"] )
                    user = decoded_bearer['user']
                except jwt.ExpiredSignatureError as e : 
                    logger.error(f"Token expired")
                    raise AuthenticationError("Token expired")
                except Exception as e:
                    logger.error('unauthorized') 
                    raise AuthenticationError('unauthorized')      
                if level[user['role']] < level[role] :
                    logger.error(f"{user['id']} with role {user['role']} doesn't have access to resource" )
                    raise ForbiddenError('insufficent role')
                logger.check(f"{user['id']} with role {user['role']} can access resource")
                logger.critical(f"{user['id']} with role {user['role']} can access resource")
                return fn(obj, info, **args)
            except Exception as e:
                error= format_error(e,info.context.headers['authorization'] )
                raise GraphQLError(message=error.get('message'), extensions=error)
        return wrapper
    return decorate