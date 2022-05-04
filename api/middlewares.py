from domain.users import get_user
from config import cfg 
import jwt

def auth_middleware(f):
    def function_wrapper(obj, info, **args):
        try :
            print(info.context.headers['authorization'].split('Bearer ')[1])
            bearer = info.context.headers['authorization'].split('Bearer ')[1]
            decoded_bearer= jwt.decode(bearer,cfg['jwt']['secret'],algorithms=["HS256"] )
            print(decoded_bearer)
            get_user(decoded_bearer['user']['id'])
        except :
            raise Exception('unauthorized')      
            
        return f(obj, info, **args)
    return function_wrapper