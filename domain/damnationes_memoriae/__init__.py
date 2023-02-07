from enum import Enum
from repository.pets import get_all_pets
import repository.damnationes_memoriae as damnationes_memoriae_data
from math import ceil
from repository.users import get_all_active_users, get_all_users
from utils.logger import logger, stringify
from datetime import datetime
import pendulum
import pydash as py_


# def create_damnatio_memoriae(data):
#     logger.domain(f'data: {stringify(data)}')
#     try:
#         damnatio_memoriae = damnationes_memoriae_data.create_damnatio_memoriae(data)
#         return damnatio_memoriae
#     except Exception as e:
#         logger.error(e)
#         raise e


# def update_damnatio_memoriae(id, data):
#     logger.domain(
#         f"id: {id}\n"
#         f"data: {stringify(data)}"
#     )
#     try:
#         damnatio_memoriae = damnationes_memoriae_data.update_damnatio_memoriae(id, data)
#         logger.check(f"damnatio_memoriae: {stringify(damnatio_memoriae)}")
#         return damnatio_memoriae
#     except Exception as e:
#         logger.error(e)
#         raise e

def get_paginated_damnationes_memoriae(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        damnationes_memoriae = get_damnationes_memoriae(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (damnationes_memoriae, pagination)
    except Exception as e:
        logger.error(e)
        raise e
  
def get_damnationes_memoriae(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        damnationes_memoriae = damnationes_memoriae_data.get_damnationes_memoriae(common_search)
        logger.output(f"damnationes_memoriae: {len(damnationes_memoriae)}")
        return damnationes_memoriae
    except Exception as e:
        logger.error(e)
        raise e


def get_damnatio_memoriae(id):
    logger.domain(f"id: {id}")
    try:
        damnatio_memoriae = damnationes_memoriae_data.get_damnatio_memoriae(id)
        logger.check(f"damnatio_memoriae: {stringify(damnatio_memoriae)}")
        return damnatio_memoriae
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        total_items = damnationes_memoriae_data.get_total_items(common_search)
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


def restore_memoriae(id):
    logger.domain(f"restoring {id}")
    try:   
        restored= damnationes_memoriae_data.restore_memoriae(id)
        logger.check(f"restored {stringify(restored)}")
        return restored
    except Exception as e: 
        logger.error(e)
        raise e