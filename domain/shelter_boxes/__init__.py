from math import ceil

import repository.shelter_boxes as shelter_boxes_data
import repository.shelter_maps as shelter_maps_data
import repository.shelter_areas as shelter_areas_data
import repository.shelter_zones as shelter_zones_data
import repository.shelter_box_occupancies as occupancies_data
import domain.shelter_zones as shelter_zones_domain
import domain.shelter_pets as shelter_pets_domain
import domain.damnationes_memoriae as damnatio_domain
from api.errors import NotFoundError, CannotDeleteWithActiveOccupancyError
from utils.logger import logger, stringify
from utils.dates import utc_now


# --- field resolvers ---
def get_area(obj, info):
    if not obj.get("area_id"):
        return None
    return shelter_areas_data.get_shelter_area(obj["area_id"])


def get_zone(obj, info):
    if not obj.get("zone_id"):
        return None
    return shelter_zones_data.get_shelter_zone(obj["zone_id"])


def _needs_cleaning(obj):
    """Empty box is NEEDS_CLEANING when a pet left after the last cleaning
    (or it was never cleaned but has been occupied)."""
    last_cleaned = obj.get("last_cleaned_at")
    last_exit = None
    for occ in occupancies_data.get_occupancies_for_box(obj["id"]):
        ex = occ.get("exited_at")
        if ex and (last_exit is None or ex > last_exit):
            last_exit = ex
    if not last_exit:
        return False
    # ISO-8601 strings in the same format compare correctly lexicographically.
    return last_cleaned is None or last_exit > last_cleaned


def get_status(obj, info):
    if obj.get("is_out_of_service"):
        return "OUT_OF_SERVICE"
    count = occupancies_data.count_active_for_box(obj["id"])
    capacity = obj.get("capacity") or 1
    if count >= capacity:
        return "FULL"
    if count > 0:
        return "OCCUPIED"
    if _needs_cleaning(obj):
        return "NEEDS_CLEANING"
    return "AVAILABLE"


def get_current_occupants(obj, info):
    active = occupancies_data.get_active_occupancies_for_box(obj["id"])
    result = []
    for occ in active:
        sp = shelter_pets_domain.get_shelter_pet(occ["shelter_pet_id"])
        if sp is not None:
            result.append(sp)
    return result


def get_occupancy_history(obj, info, **kwargs):
    items = occupancies_data.get_occupancies_for_box(obj["id"])
    pagination = {
        "total_items": len(items),
        "total_pages": 1,
        "current_page": 0,
        "page_size": len(items),
    }
    return {"success": True, "items": items, "pagination": pagination}


# --- helpers ---
def shelter_id_for_box(box_id):
    box = shelter_boxes_data.get_shelter_box(box_id)
    shelter_map = shelter_maps_data.get_shelter_map(box["map_id"])
    return shelter_map["shelter_id"]


# --- business ---
def create_shelter_box(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter_map = shelter_maps_data.get_shelter_map(data.get("map_id"))
        if shelter_map is None:
            raise NotFoundError(f'no shelter_map found with id {data.get("map_id")}')
        shelter_zones_domain.assert_zone_on_map(data.get("zone_id"), data.get("map_id"))
        return shelter_boxes_data.create_shelter_box(data)
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_box(id, data):
    logger.domain(f"id: {id}\ndata: {stringify(data)}")
    try:
        clean = {k: v for k, v in data.items() if v is not None}
        return shelter_boxes_data.update_shelter_box(id, clean)
    except Exception as e:
        logger.error(e)
        raise e


def mark_box_cleaned(id):
    from datetime import datetime
    return shelter_boxes_data.update_shelter_box(id, {
        "last_cleaned_at": utc_now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    })


def set_box_out_of_service(id, out_of_service):
    return shelter_boxes_data.update_shelter_box(id, {"is_out_of_service": out_of_service})


def delete_shelter_box(id, user_id):
    logger.domain(f"id: {id} remove")
    try:
        box = shelter_boxes_data.get_shelter_box(id)
        if occupancies_data.count_active_for_box(id) > 0:
            raise CannotDeleteWithActiveOccupancyError(
                "box has active pet occupancy; release the pets first"
            )
        return damnatio_domain.delete_row(id, 'shelter_boxes', box, user_id)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_box(id):
    return shelter_boxes_data.get_shelter_box(id)


def get_paginated_shelter_boxes(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        boxes = shelter_boxes_data.get_shelter_boxes(common_search)
        return (boxes, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    try:
        total_items = shelter_boxes_data.get_total_items(common_search)
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
