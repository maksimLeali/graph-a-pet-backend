import data.users as users_data
from data.ownerships.models import Ownership, CustodyRole
import domain.pets as pets_domain
import domain.ownerships as ownerships_domain
from passlib.hash import pbkdf2_sha256 
import jwt
from config import cfg

def get_ownerships(obj, info):    
    return ownerships_domain.get_filtered_ownerships({"user_id": obj['id']})

def create_user(data):
    
    return users_data.create_user(data)

def update_user(id, data):
    return users_data.update_user(id, data)

def get_users():
    return users_data.get_users()

def get_user(id): 
    return users_data.get_user(id)

def add_pet_to_user(user_id, pet):
    user= users_data.get_user(user_id)
    if(not user):
        raise Exception(f"no user found with id: {user_id}")
    new_pet = pets_domain.create_pet(pet)
    ownership = {
        "user_id" : user['id'],
        "pet_id": new_pet['id'],
        "custody_level": CustodyRole.OWNER.name
    }
    new_ownership = ownerships_domain.create_ownership(ownership)
    return (new_pet, new_ownership)

async def login(email, password) -> str:
    user= await users_data.get_user_from_email(email)
    if(pbkdf2_sha256.verify(password, user['password'])):
        return jwt.encode({"user" : user},cfg['jwt']['secret'], algorithm="HS256" )
    raise Exception('Credentials error')
    
    
    