from ariadne import convert_kwargs_to_snake_case
import data.statistics as statistics_data
from math import ceil
from time import time
from libs.logger import logger, stringify
from api.errors import AuthenticationError, InternalError, NotFoundError
from data.ownerships.models import CustodyLevel
import domain.pets as pets_domain
import domain.ownerships as ownerships_domain
import domain.medias as media_domain
from passlib.hash import pbkdf2_sha256
import jwt
from datetime import datetime, timedelta
import pydash as py_
from config import cfg



def create_statistic(data):
    logger.domain(f'data: {stringify(data)}')
    try:
        statistic = statistics_data.create_statistic(data)
        return statistic
    except Exception as e:
        logger.error(e)
        raise e


def update_statistic(id, data):
    logger.domain(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        statistic = statistics_data.update_statistic(id, data)
        logger.check(f"statistic: {stringify(statistic)}")
        return statistic
    except Exception as e:
        logger.error(e)
        raise e

def get_today_statistics():
    logger.domain('get today statistics')
    try: 
        today_statistics = statistics_data.get_statistics({"filters": {} ,"pagination" : {"page": 0, "page_size" : 1 }, "ordering" : { "order_by": "date", "order_direction" :"desc"} })[0]
        this_month_statistics = statistics_data.get_statistics({"filters": { "and": { "ranges" : { "date" : {"min" : str(datetime.today() - timedelta(days=30))}}} } ,"pagination" : {"page": 0, "page_size" : 30 }, "ordering" : { "order_by": "date", "order_direction" :"desc"} })
        labels = py_.map_(this_month_statistics, 'date')
        # 3 : 100 = 2 : x 
        response = {
            "active_users": today_statistics.get("active_per_day"),
            "all_pets": today_statistics.get("all_pets"),
            "all_users": today_statistics.get("all_users"),
            "active_users_percent": "{0:.2f}".format(( today_statistics.get("active_per_day") / today_statistics.get("all_users")  )* 100 ) ,
            "active_users_stats": {
                "data": py_.map_(this_month_statistics, 'active_per_day'),
                "labels": labels,
            },
            "all_pet_stats": {
                "data": py_.map_(this_month_statistics, 'all_pets'),
                "labels": labels,
            },
            "all_users_stats": {
                "data": py_.map_(this_month_statistics, 'all_users'),
                "labels": labels,
            },
            "active_users_percent_stats": {
                "data": py_.map_(this_month_statistics, lambda stat : "{0:.2f}".format((stat.get("active_per_day") / stat.get("all_users"))*100 )),
                "labels": labels,
            }
        }
        logger.check(stringify(response))
        return response
    except Exception as e : 
        logger.error(e)
        raise e

def get_paginated_statistics(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        statistics = get_statistics(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (statistics, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_statistics(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        statistics = statistics_data.get_statistics(common_search)
        logger.output(f"statistics: {len(statistics)}")
        return statistics
    except Exception as e:
        logger.error(e)
        raise e


def get_statistic(id):
    logger.domain(f"id: {id}")
    try:
        statistic = statistics_data.get_statistic(id)
        logger.check(f"statistic: {stringify(statistic)}")
        return statistic
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        total_items = statistics_data.get_total_items(common_search)
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


def add_pet_to_statistic(statistic_id, pet, custody_level=CustodyLevel.SUB_OWNER.name):
    logger.domain(
        f"statistic_id: {statistic_id}\n"
        f"pet: {stringify(pet)}"
    )
    try:
        statistic = statistics_data.get_statistic(statistic_id)
        if(not statistic):
            raise NotFoundError(f"no statistic found with id: {statistic_id}")
        new_pet = pets_domain.create_pet(pet)
        ownership = {
            "statistic_id": statistic['id'],
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
        statistic = statistics_data.get_statistic_from_email(email)
        logger.domain(f"verofiyg statistic: {statistic['email']}")
        if(pbkdf2_sha256.verify(password, statistic['password'])):
            logger.check(f"statistic verified : {stringify(statistic)}")
            statistics_data.update_statistic(statistic.get('id'), {"last_login": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')  })
            return jwt.encode(
                {"statistic": py_.omit(statistic, "password"),
                 "iat": int(time()),
                 "exp": int(time()) + 7 * 24*60*60
                 },
                cfg['jwt']['secret'], algorithm="HS256"), statistic
        raise AuthenticationError('Credentials error')
    except Exception as e:
        logger.error(e)
        raise e
