from math import ceil

import repository.shelter_map_elements as elements_data
import repository.shelter_maps as shelter_maps_data
import domain.damnationes_memoriae as damnatio_domain
from api.errors import NotFoundError
from utils.logger import logger, stringify


# --- helpers ---
def shelter_id_for_element(element_id):
    element = elements_data.get_shelter_map_element(element_id)
    shelter_map = shelter_maps_data.get_shelter_map(element["map_id"])
    return shelter_map["shelter_id"]


# --- business ---
def create_shelter_map_element(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter_map = shelter_maps_data.get_shelter_map(data.get("map_id"))
        if shelter_map is None:
            raise NotFoundError(f'no shelter_map found with id {data.get("map_id")}')
        return elements_data.create_shelter_map_element(data)
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_map_element(id, data):
    logger.domain(f"id: {id}\ndata: {stringify(data)}")
    try:
        clean = {k: v for k, v in data.items() if v is not None}
        return elements_data.update_shelter_map_element(id, clean)
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_map_element(id, user_id):
    logger.domain(f"id: {id} remove")
    try:
        element = elements_data.get_shelter_map_element(id)
        return damnatio_domain.delete_row(id, 'shelter_map_elements', element, user_id)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_map_element(id):
    return elements_data.get_shelter_map_element(id)


def get_paginated_shelter_map_elements(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        elements = elements_data.get_shelter_map_elements(common_search)
        return (elements, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    try:
        total_items = elements_data.get_total_items(common_search)
        page_size = common_search["pagination"]["page_size"]
        total_pages = ceil(total_items / page_size)
        current_page = common_search["pagination"]["page"]
        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error(e)
        raise e
