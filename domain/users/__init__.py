from ariadne import convert_kwargs_to_snake_case
import repository.users as users_data
from math import ceil
from time import time
from utils.logger import logger, stringify
from controller.errors import AuthenticationError, InternalError, NotFoundError
import repository.damnationes_memoriae as damnatio
from repository.ownerships.models import CustodyLevel
import domain.pets as pets_domain
import domain.ownerships as ownerships_domain
import domain.medias as media_domain
from passlib.hash import pbkdf2_sha256
import jwt
from datetime import datetime
import pydash as py_
from config import cfg


@convert_kwargs_to_snake_case
def get_profile_pic(user_id: str):
    logger.domain(f"id {user_id}")
    try:
        medias = media_domain.get_medias({"ordering": {"order_direction": "ASC", "order_by": "created_at"}, "pagination": {
                                        "page_size": 10, "page": 0}, "filters": {"and": {"fixed": {"ref_id ": user_id, "scope": "profile_picture"}}}})
        media= medias[0]
        logger.check(media)
        return media
    except Exception as e:
        logger.error(e)
        raise e


@convert_kwargs_to_snake_case
def get_ownerships(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        ownerships, pagination = ownerships_domain.get_paginated_ownerships(
            common_search)
        logger.check(
            f"response: {stringify({'ownerships' : ownerships , 'pagination': pagination}) }")
        return (ownerships, pagination)
    except Exception as e:
        logger.error(e)
        raise e


@convert_kwargs_to_snake_case
def count_ownerships(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = ownerships_domain.get_pagination(common_search)
        logger.check(f"response: {stringify({'ownerships' :  pagination}) }")
        return (pagination.get("total_items", 0))
    except Exception as e:
        logger.error(e)
        raise e


def create_user(data):
    logger.domain(f'data: {stringify(data)}')
    try:
        user = users_data.create_user(data)
        return user
    except Exception as e:
        logger.error(e)
        raise e


def update_user(id, data):
    logger.domain(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        user = users_data.update_user(id, data)
        logger.check(f"user: {stringify(user)}")
        return user
    except Exception as e:
        logger.error(e)
        raise e
    
def update_user_activity(id):
    logger.domain(f"id: {id}")
    try:
        user = users_data.update_user(id, {"last_activity" :datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ') })
        logger.check(f"user: {stringify(user)}")
        return user
    except Exception as e:
        logger.error(e)
        raise e

def delete_user(id, ):
    logger.domain(f"id {id} remove ")
    try: 
        user = users_data.get_user(id)
        memoriae_id = damnatio.create_damnatio_memoriae({"original_data": user, 'original_table': 'users'})
        users_data.delete_user(id)
        return memoriae_id
    except Exception as e:
        logger.error(e)
        raise e

def get_paginated_users(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        users = get_users(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (users, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_users(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        users = users_data.get_users(common_search)
        logger.output(f"users: {len(users)}")
        return users
    except Exception as e:
        logger.error(e)
        raise e


def get_user(id):
    logger.domain(f"id: {id}")
    try:
        user = users_data.get_user(id)
        logger.check(f"user: {stringify(user)}")
        return user
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        total_items = users_data.get_total_items(common_search)
        page_size = common_search['pagination']['page_size']
        total_pages = ceil(total_items / page_size)
        current_page = common_search['pagination']['page']
        pagination = {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size
        }
        logger.output(f"pagination: {stringify(pagination)}")
        return pagination
    except Exception as e:
        logger.error(e)
        raise e


def add_pet_to_user(user_id, pet, custody_level=CustodyLevel.SUB_OWNER.name):
    logger.domain(
        f"user_id: {user_id}\n"
        f"pet: {stringify(pet)}"
    )
    try:
        user = users_data.get_user(user_id)
        if(not user):
            raise NotFoundError(f"no user found with id: {user_id}")
        new_pet = pets_domain.create_pet(pet)
        ownership = {
            "user_id": user['id'],
            "pet_id": new_pet['id'],
            "custody_level": custody_level
        }
        new_ownership = ownerships_domain.create_ownership(ownership)
        return (new_pet, new_ownership)
    except Exception as e:
        logger.error(e)
        raise e


def login(email, password) -> str:
    logger.domain(f"email: {email}, password: {password}")
    try:
        user = users_data.get_user_from_email(email)
        logger.domain(f"verofiyg user: {user['email']}")
        if(pbkdf2_sha256.verify(password, user['password'])):
            logger.check(f"user verified : {stringify(user)}")
            today = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            users_data.update_user(user.get('id'), {"last_login": today,"last_activity":today   })
            return jwt.encode(
                {"user": py_.omit(user, "password"),
                 "iat": int(time()),
                 "exp": int(time()) + 7 * 24*60*60
                 },
                cfg['jwt']['secret'], algorithm="HS256"), user
        raise AuthenticationError('Credentials error')
    except Exception as e:
        logger.error(e)
        raise e
