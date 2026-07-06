from math import ceil

import repository.shelter_box_occupancies as occupancies_data
import domain.shelter_boxes as shelter_boxes_domain
import domain.shelter_pets as shelter_pets_domain
import domain.users as users_domain
from api.errors import NotFoundError, BadRequest
from utils.logger import logger, stringify


# --- field resolvers ---
def get_box(obj, info):
    return shelter_boxes_domain.get_shelter_box(obj["box_id"])


def get_shelter_pet(obj, info):
    return shelter_pets_domain.get_shelter_pet(obj["shelter_pet_id"])


def get_moved_by(obj, info):
    if not obj.get("moved_by_id"):
        return None
    return users_domain.get_user(obj["moved_by_id"])


# --- helpers ---
def shelter_id_for_box(box_id):
    return shelter_boxes_domain.shelter_id_for_box(box_id)


def shelter_id_for_occupancy(occupancy_id):
    occ = occupancies_data.get_occupancy(occupancy_id)
    return shelter_boxes_domain.shelter_id_for_box(occ["box_id"])


# --- business ---
def _assert_can_admit(box, shelter_pet_id):
    if box.get("is_out_of_service"):
        raise BadRequest("box is out of service")
    capacity = box.get("capacity") or 1
    if occupancies_data.count_active_for_box(box["id"]) >= capacity:
        raise BadRequest("box is full")


def assign_pet_to_box(box_id, shelter_pet_id, moved_by_id=None, reason=None):
    logger.domain(f"assign pet {shelter_pet_id} -> box {box_id}")
    try:
        box = shelter_boxes_domain.get_shelter_box(box_id)
        sp = shelter_pets_domain.get_shelter_pet(shelter_pet_id)
        if sp is None:
            raise NotFoundError(f"no shelter_pet found with id {shelter_pet_id}")
        if occupancies_data.get_active_occupancy_for_pet(shelter_pet_id) is not None:
            raise BadRequest("pet already has an active occupancy; release or move it first")
        _assert_can_admit(box, shelter_pet_id)
        return occupancies_data.create_occupancy(box_id, shelter_pet_id, moved_by_id, reason)
    except Exception as e:
        logger.error(e)
        raise e


def release_pet_from_box(occupancy_id, moved_by_id=None, reason=None):
    logger.domain(f"release occupancy {occupancy_id}")
    try:
        return occupancies_data.close_occupancy(occupancy_id, moved_by_id, reason)
    except Exception as e:
        logger.error(e)
        raise e


def move_pet_between_boxes(shelter_pet_id, to_box_id, moved_by_id=None, reason=None):
    logger.domain(f"move pet {shelter_pet_id} -> box {to_box_id}")
    try:
        to_box = shelter_boxes_domain.get_shelter_box(to_box_id)
        sp = shelter_pets_domain.get_shelter_pet(shelter_pet_id)
        if sp is None:
            raise NotFoundError(f"no shelter_pet found with id {shelter_pet_id}")
        _assert_can_admit(to_box, shelter_pet_id)
        return occupancies_data.move_pet_between_boxes(shelter_pet_id, to_box_id, moved_by_id, reason)
    except Exception as e:
        logger.error(e)
        raise e


def get_current_box_for_pet(shelter_pet_id):
    active = occupancies_data.get_active_occupancy_for_pet(shelter_pet_id)
    if active is None:
        return None
    return shelter_boxes_domain.get_shelter_box(active["box_id"])


def get_occupancy(id):
    return occupancies_data.get_occupancy(id)


def get_paginated_occupancies(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        items = occupancies_data.get_occupancies(common_search)
        return (items, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    try:
        total_items = occupancies_data.get_total_items(common_search)
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
