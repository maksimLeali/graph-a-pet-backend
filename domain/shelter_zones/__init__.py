from math import ceil

import repository.shelter_zones as shelter_zones_data
import repository.shelter_areas as shelter_areas_data
import repository.shelter_boxes as shelter_boxes_data
import repository.shelter_maps as shelter_maps_data
import domain.damnationes_memoriae as damnatio_domain
from api.errors import NotFoundError, BadRequest
from utils.logger import logger, stringify


# --- field resolvers ---
def get_areas(obj, info):
    return shelter_areas_data.get_areas_by_zone(obj["id"])


def get_boxes(obj, info):
    return shelter_boxes_data.get_boxes_by_zone(obj["id"])


# --- helpers ---
def shelter_id_for_zone(zone_id):
    zone = shelter_zones_data.get_shelter_zone(zone_id)
    shelter_map = shelter_maps_data.get_shelter_map(zone["map_id"])
    return shelter_map["shelter_id"]


def assert_zone_on_map(zone_id, map_id):
    """Verifica che la zona esista e appartenga alla mappa indicata."""
    zone = shelter_zones_data.get_shelter_zone(zone_id)
    if zone is None:
        raise NotFoundError(f"no shelter_zone found with id {zone_id}")
    if zone["map_id"] != map_id:
        raise BadRequest(f"zone {zone_id} does not belong to map {map_id}")
    return zone


# --- business ---
def create_shelter_zone(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter_map = shelter_maps_data.get_shelter_map(data.get("map_id"))
        if shelter_map is None:
            raise NotFoundError(f'no shelter_map found with id {data.get("map_id")}')
        return shelter_zones_data.create_shelter_zone(data)
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_zone(id, data):
    logger.domain(f"id: {id}\ndata: {stringify(data)}")
    try:
        clean = {k: v for k, v in data.items() if v is not None}
        return shelter_zones_data.update_shelter_zone(id, clean)
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_zone(id, user_id):
    logger.domain(f"id: {id} remove")
    try:
        zone = shelter_zones_data.get_shelter_zone(id)
        return damnatio_domain.delete_row(id, 'shelter_zones', zone, user_id)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_zone(id):
    return shelter_zones_data.get_shelter_zone(id)


def get_paginated_shelter_zones(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        zones = shelter_zones_data.get_shelter_zones(common_search)
        return (zones, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    try:
        total_items = shelter_zones_data.get_total_items(common_search)
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
