from ariadne import convert_kwargs_to_snake_case
import data.users as users_data
from math import ceil
from time import time
from libs.logger import logger, stringify
from api.errors import AuthenticationError, InternalError
from data.ownerships.models import CustodyLevel
import domain.pets as pets_domain
import domain.ownerships as ownerships_domain
from passlib.hash import pbkdf2_sha256
import jwt
import pydash as py_
from config import cfg

@convert_kwargs_to_snake_case
def get_ownerships(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        ownerships, pagination = ownerships_domain.get_paginated_ownerships(common_search)
        logger.check(f"response: {stringify({'ownerships' : ownerships , 'pagination': pagination}) }")
        return (ownerships, pagination)
    except Exception as e : 
        logger.error(e)
        raise e

def create_user(data):
    return users_data.create_user(data)


def update_user(id, data):
    return users_data.update_user(id, data)


def get_paginated_users(common_search):
    try:
        pagination = get_pagination(common_search)
        users = get_users(common_search)

        return (users, pagination)
    except Exception as e: 
        logger.error(e)
        raise e

def get_users(common_search):
    try: 
        return users_data.get_users(common_search)
    except Exception as e:
        raise e

def get_user(id):
    try:
        return users_data.get_user(id)
    except Exception as e:
        logger.error(e)
        raise e

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
        raise e

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


def login(email, password) -> str:
    logger.domain(f"email: {email}, password: {password}")
    try:
        user = users_data.get_user_from_email(email)
        logger.domain(f"verofiyg user: {user['email']}")
        if(pbkdf2_sha256.verify(password, user['password'])):
            logger.check("user verified")
            return jwt.encode(
                        {"user": py_.omit(user, "password"),
                         "iat": int(time()),
                         "exp": int(time()) + 7 * 24*60*60
                        }, 
                    cfg['jwt']['secret'], algorithm="HS256"), user
        raise AuthenticationError('Credentials error')
    except Exception as e:
        logger.error("Credential errors")
        raise e
