import repository.damnationes_memoriae as damnationes_memoriae_data
from math import ceil
from utils.logger import logger, stringify


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
        damnationes_memoriae = damnationes_memoriae_data.get_damnationes_memoriae(
            common_search
        )
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
        page_size = common_search["pagination"]["page_size"]
        total_pages = ceil(total_items / page_size)
        current_page = common_search["pagination"]["page"]
        pagination = {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size,
        }
        logger.output(f"pagination: {stringify(pagination)}")
        return pagination
    except Exception as e:
        logger.error(e)
        raise e


def restore_memoriae(id, user):
    logger.domain(f"{user['id'] }({user['role']}) is restoring {id}")
    try:
        restored, table = damnationes_memoriae_data.restore_memoriae(id, user)
        logger.check(f"restored {stringify(restored)}")
        return restored, table
    except Exception as e:
        logger.error(e)
        raise e


def delete_row(id, table, data, user_id ):
    logger.domain(f"{user_id} is removing {id} from {table}")
    try:
        memoriae_id, skip = damnationes_memoriae_data.delete_row(id, table,data, user_id)
        
        logger.check(f"memoriae created : {memoriae_id}")
        return memoriae_id
    except Exception as e:
        logger.error(e)
        raise e
