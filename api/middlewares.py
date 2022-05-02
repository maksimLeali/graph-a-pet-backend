from domain.users import get_user
from config import cfg 


def auth_middleware(f):
    def function_wrapper(obj, info):
        try :
            bearer = info.context.headers['authorization'].split('Bearer ')[1]
            decoded_bearer= jwt.decode(bearer,cfg['jwt']['secret'],algorithms=["HS256"] )
            get_user(decoded_bearer['user']['id'])
        except :
            raise Exception('unauthorized')      
            
        return f(obj, info)
    return function_wrapper