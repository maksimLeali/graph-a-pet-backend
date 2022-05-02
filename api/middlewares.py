from domain.users import get_user
import yaml
import jwt

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)


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