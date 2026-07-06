from math import ceil

import repository.shelter_maps as shelter_maps_data
import repository.shelter_boxes as shelter_boxes_data
import repository.shelter_areas as shelter_areas_data
import repository.shelter_map_elements as shelter_map_elements_data
import domain.shelters as shelters_domain
import domain.medias as medias_domain
import domain.damnationes_memoriae as damnatio_domain
from api.errors import NotFoundError
from utils.logger import logger, stringify


# --- field resolvers ---
def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj["shelter_id"])


def get_areas(obj, info):
    return shelter_areas_data.get_areas_by_map(obj["id"])


def get_elements(obj, info):
    return shelter_map_elements_data.get_elements_by_map(obj["id"])


def get_background_media(obj, info):
    if not obj.get("background_media_id"):
        return None
    return medias_domain.get_media(obj["background_media_id"])


def get_boxes(obj, info):
    return shelter_boxes_data.get_boxes_by_map(obj["id"])


# --- business ---
def create_shelter_map(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter = shelters_domain.get_shelter(data.get("shelter_id"))
        if shelter is None:
            raise NotFoundError(f'no shelter found with id {data.get("shelter_id")}')
        return shelter_maps_data.create_shelter_map(data)
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_map(id, data):
    logger.domain(f"id: {id}\ndata: {stringify(data)}")
    try:
        clean = {k: v for k, v in data.items() if v is not None}
        return shelter_maps_data.update_shelter_map(id, clean)
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_map(id, user_id):
    logger.domain(f"id: {id} remove")
    try:
        shelter_map = shelter_maps_data.get_shelter_map(id)
        return damnatio_domain.delete_row(id, 'shelter_maps', shelter_map, user_id)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_map(id):
    return shelter_maps_data.get_shelter_map(id)


def save_layout(map_id, data):
    logger.domain(f"map_id: {map_id}")
    try:
        shelter_map = shelter_maps_data.get_shelter_map(map_id)
        if shelter_map is None:
            raise NotFoundError(f"no shelter_map found with id {map_id}")
        return shelter_maps_data.save_layout(map_id, data)
    except Exception as e:
        logger.error(e)
        raise e


def get_paginated_shelter_maps(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        maps = shelter_maps_data.get_shelter_maps(common_search)
        return (maps, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    try:
        total_items = shelter_maps_data.get_total_items(common_search)
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
