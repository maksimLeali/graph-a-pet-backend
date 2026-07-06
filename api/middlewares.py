from enum import Enum
from functools import wraps
from typing import Any

from graphql import GraphQLError, GraphQLResolveInfo
from api.errors import AuthenticationError, ForbiddenError, format_error
from domain.users import get_user, update_user_activity
from time import time
from utils.logger import logger
from utils import get_request_user
from repository.users.models import UserRole
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
            
        update_user_activity(decoded_bearer.get('user').get('id'))
        return f(obj, info, **args)
    return function_wrapper

SHELTER_ROLE_LEVEL = {"OWNER": 4, "MANAGER": 3, "STAFF": 2, "VOLUNTEER": 1}


def get_user_shelter_level(user_id, shelter_id):
    """Livello massimo (int) dello user su uno shelter; 0 se nessun ruolo."""
    # import ritardato: evita import circolare middlewares -> domain -> api
    import domain.shelter_roles as shelter_roles_domain
    roles = shelter_roles_domain.get_user_roles_on_shelter(user_id, shelter_id) or []
    levels = [SHELTER_ROLE_LEVEL.get((r.get("role") or "").upper(), 0) for r in roles]
    return max(levels) if levels else 0


def assert_shelter_role(token, shelter_id, role: str):
    """Verifica che l'utente del token abbia almeno <role> su <shelter_id>.
    ADMIN globale passa sempre. Solleva ForbiddenError altrimenti."""
    user = get_request_user(token)
    if user.get("role") == UserRole.ADMIN.name:
        return user
    required = SHELTER_ROLE_LEVEL[role]
    if get_user_shelter_level(user["id"], shelter_id) < required:
        logger.error(f"{user['id']} lacks shelter role {role} on {shelter_id}")
        raise ForbiddenError("insufficient shelter role")
    return user


def min_shelter_role(role: str):
    """Decoratore: richiede almeno <role> (RoleLevel) sullo shelter_id passato
    come argomento del resolver o dentro data['shelter_id']."""
    def decorate(fn):
        @wraps(fn)
        def wrapper(obj: Any, info: GraphQLResolveInfo, **args):
            try:
                token = info.context.headers['authorization']
                shelter_id = args.get("shelter_id")
                if shelter_id is None and isinstance(args.get("data"), dict):
                    shelter_id = args["data"].get("shelter_id")
                if shelter_id is None:
                    raise ForbiddenError("shelter_id required for authorization")
                assert_shelter_role(token, shelter_id, role)
                return fn(obj, info, **args)
            except Exception as e:
                error = format_error(e, info.context.headers['authorization'])
                raise GraphQLError(message=error.get('message'), extensions=error)
        return wrapper
    return decorate


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
                update_user_activity(user.get('id'))
                return fn(obj, info, **args)
            except Exception as e:
                error= format_error(e,info.context.headers['authorization'] )
                raise GraphQLError(message=error.get('message'), extensions=error)
        return wrapper
    return decorate