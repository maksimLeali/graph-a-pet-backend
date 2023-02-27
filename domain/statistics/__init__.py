from enum import Enum
from repository.pets import get_all_pets
import repository.statistics as statistics_data
from math import ceil
from repository.users import get_all_active_users, get_all_users
from repository.reports import get_all_reports, get_daily_reports
from utils.logger import logger, stringify
import pendulum
import pydash as py_

class CoatLength(Enum) :
    DAILY = "day",
    WEEKLY = "week",
    MONTHLY = "month"
    

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
        this_month_statistics = statistics_data.get_dashboard()
        labels = py_.map_(this_month_statistics, 'date')
        response = {
            "active_users": today_statistics.get("active_users"),
            "all_pets": today_statistics.get("all_pets"),
            "all_users": today_statistics.get("all_users"),
            "active_users_mean": int(py_.mean(py_.map_(this_month_statistics, 'active_users'))),
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
    
def get_statistics_by_group(date_from, date_to, group_type):
    logger.domain(f"from {date_from} to {date_to}")
    try: 
        this_range_statistics = statistics_data.get_statistics({"filters": { "and": { "ranges" : { "date" : {"min" : date_from, "max" : date_to }}} } ,"pagination" : {"page": 0, "page_size" : 100 }, "ordering" : { "order_by": "date", "order_direction" :"asc"} })
        logger.info(this_range_statistics)
        statistics = {
            "labels" : [],
            "active_users_mean" : [],
            "active_users_min" : [],
            "active_users_max" : [],
            "all_users": [],
            "all_pets": [],
        }
        date_groups = {}
        for record in this_range_statistics :
            group = pendulum.parse(record.get("date")).start_of(group_type).format("YYYY-MM-DD")
            if date_groups.get(group) == None :
                date_groups[group]= []
            date_groups[group].append(record)
        for key in date_groups.keys():
            statistics["labels"].append(key)
            statistics["active_users_mean"].append( "{0:.2f}".format(py_.mean_by(date_groups[key], "active_users")))
            statistics["all_pets"].append( "{0:.2f}".format(py_.mean_by(date_groups[key], "all_pets")))
            statistics["all_users"].append( "{0:.2f}".format(py_.mean_by(date_groups[key], "all_users")))
            statistics["active_users_max"].append( "{0:.2f}".format(py_.max_by(date_groups[key], "active_users")["active_users"]))
            statistics["active_users_min"].append( "{0:.2f}".format(py_.min_by(date_groups[key], "active_users")["active_users"]))
        
        logger.check(stringify(statistics))
        return statistics
    except Exception as e :
        logger.error(e)
        raise e

def get_real_time_statistic():
    logger.domain('get real time stats')
    try:
        active_users = len(get_all_active_users())
        all_users = len(get_all_users())
        all_pets = len(get_all_pets())
        all_reports = len(get_all_reports())
        daily_reports= len(get_daily_reports())
        data =  {
            "active_users" :  active_users,
            "all_users" :   all_users,
            "all_pets" :   all_pets,
            "all_reports" :   all_reports,
            "daily_reports": daily_reports,
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


