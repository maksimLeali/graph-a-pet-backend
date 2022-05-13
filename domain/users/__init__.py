from ariadne import convert_kwargs_to_snake_case
import data.users as users_data
from math import ceil
from libs.logger import logger
from data.ownerships.models import Ownership, CustodyLevel
import domain.pets as pets_domain
import domain.ownerships as ownerships_domain
from passlib.hash import pbkdf2_sha256
import jwt
from config import cfg
from libs.utils import format_common_search

@convert_kwargs_to_snake_case
def get_ownerships(obj, info, common_search):
    common_search= format_common_search(common_search)
    common_search['filters']['fixeds']['user_id'] = obj['id']
    ownerships, pagination = ownerships_domain.get_paginated_ownerships(common_search)
    return { "items": ownerships, "pagination": pagination}


def create_user(data):

    return users_data.create_user(data)


def update_user(id, data):
    return users_data.update_user(id, data)


def get_paginated_users(common_search):
    pagination = get_pagination(common_search)
    users = get_users(common_search)

    return (users, pagination)


def get_users(common_search):
    return users_data.get_users(common_search)


def get_user(id):
    return users_data.get_user(id)


def get_pagination(common_search):
    try: 
        total_items = users_data.get_total_items(common_search)
        page_size = common_search['pagination']['page_size']
        total_pages = ceil(total_items /page_size)
        current_page = common_search['pagination']['page']
        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(e)
        raise Exception(e)

def add_pet_to_user(user_id, pet):
    user = users_data.get_user(user_id)
    if(not user):
        raise Exception(f"no user found with id: {user_id}")
    new_pet = pets_domain.create_pet(pet)
    ownership = {
        "user_id": user['id'],
        "pet_id": new_pet['id'],
        "custody_level": CustodyLevel.OWNER.name
    }
    new_ownership = ownerships_domain.create_ownership(ownership)
    return (new_pet, new_ownership)


async def login(email, password) -> str:
    try:
        user = await users_data.get_user_from_email(email)
        if(pbkdf2_sha256.verify(password, user['password'])):
            return jwt.encode({"user": user}, cfg['jwt']['secret'], algorithm="HS256")
        raise Exception
    except:
        raise Exception('Credentials error')
