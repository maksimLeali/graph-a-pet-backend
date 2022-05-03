import data.users as users_data
from passlib.hash import pbkdf2_sha256 
import jwt
from config import cfg

def get_user_ownerships(obj, info):
    return []

def create_user(data):
    
    return users_data.create_user(data)

def update_user(id, data):
    return users_data.update_user(id, data)

def get_users():
    return users_data.get_users()

def get_user(id): 
    return users_data.get_user(id).to_dict()

def create_dog_to_user(user_id, dog):
    return "ok"

async def login(email, password) -> str:
    user= await users_data.get_user_from_email(email)
    if(pbkdf2_sha256.verify(password, user['password'])):
        return jwt.encode({"user" : user},cfg['jwt']['secret'], algorithm="HS256" )
    raise Exception('Credentials error')
    
    
    