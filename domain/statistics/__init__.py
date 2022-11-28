from data.pets import get_all_pets
import data.statistics as statistics_data
from math import ceil
from data.users import get_all_active_users, get_all_users
from libs.logger import logger, stringify
from datetime import datetime, timedelta
import pydash as py_



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
        this_month_statistics = statistics_data.get_statistics({"filters": { "and": { "ranges" : { "date" : {"min" : str(datetime.today().replace(day=1))}}} } ,"pagination" : {"page": 0, "page_size" : 31 }, "ordering" : { "order_by": "date", "order_direction" :"asc"} })
        labels = py_.map_(this_month_statistics, 'date')
        # 3 : 100 = 2 : x 
        response = {
            "active_users": today_statistics.get("active_users"),
            "all_pets": today_statistics.get("all_pets"),
            "all_users": today_statistics.get("all_users"),
            "active_users_percent": "{0:.2f}".format(( today_statistics.get("active_users") / today_statistics.get("all_users")  )* 100 ) ,
            "labels": labels,
            "active_users_stats": py_.map_(this_month_statistics, 'active_users'),
            "all_pet_stats": py_.map_(this_month_statistics, 'all_pets'),
            "all_users_stats":  py_.map_(this_month_statistics, 'all_users'),
            "active_users_percent_stats": py_.map_(this_month_statistics, lambda stat : "{0:.2f}".format((stat.get("active_users") / stat.get("all_users"))*100 )),
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

def get_real_time_statistic():
    logger.domain('get real time stats')
    try:
        active_users = len(get_all_active_users())
        all_users = len(get_all_users())
        all_pets = len(get_all_pets())
        data =  {
            "active_users" :  active_users,
            "all_users" :   all_users,
            "all_pets" :   all_pets,
            "active_users_percent" : "{0:.2f}".format((active_users / all_users  )* 100 ) ,
        }
        return data
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


