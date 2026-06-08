import repository.shelters as shelters_data
from math import ceil
from utils.logger import logger, stringify
import domain.damnationes_memoriae as damnatio_domain
import pydash as py_


SHELTER_UPDATE_FIELDS = [
    "name", "street", "street_number", "city",
    "province_code", "postal_code", "region", "district", "contacts",
]


def create_shelter(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter = shelters_data.create_shelter(data)
        logger.check(f"shelter: {stringify(shelter)}")
        return shelter
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter(id, data):
    logger.domain(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        shelter = shelters_data.update_shelter(id, py_.pick(data, SHELTER_UPDATE_FIELDS))
        logger.check(f"shelter: {stringify(shelter)}")
        return shelter
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter(id, user_id):
    logger.domain(f"id {id} remove")
    try:
        shelter = shelters_data.get_shelter(id)
        damnatio_id = damnatio_domain.delete_row(id, 'shelters', shelter, user_id)
        return damnatio_id
    except Exception as e:
        logger.error(e)
        raise e


def get_paginated_shelters(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        shelters = get_shelters(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (shelters, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelters(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        shelters = shelters_data.get_shelters(common_search)
        logger.output(f"shelters: {len(shelters)}")
        return shelters
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter(id):
    logger.domain(f"id: {id}")
    try:
        shelter = shelters_data.get_shelter(id)
        logger.check(f"shelter: {stringify(shelter)}")
        return shelter
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        total_items = shelters_data.get_total_items(common_search)
        page_size = common_search['pagination']['page_size']
        total_pages = ceil(total_items / page_size)
        current_page = common_search['pagination']['page']
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
