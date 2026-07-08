from math import ceil

import repository.shelter_inventory_items as items_data
import repository.shelter_inventory_movements as movements_data
import domain.shelters as shelters_domain
import domain.users as users_domain
import domain.damnationes_memoriae as damnatio_domain
from api.errors import (
    NotFoundError,
    BadRequest,
    InsufficientStockError,
    CannotDeleteWithHistoryError,
)
from utils.logger import logger, stringify

NEGATIVE_TYPES = {"CONSUMPTION", "WASTE"}
POSITIVE_TYPES = {"RESTOCK", "DONATION"}


def apply_sign(movement_type, quantity):
    q = abs(quantity)
    if movement_type in NEGATIVE_TYPES:
        return -q
    if movement_type in POSITIVE_TYPES:
        return q
    # ADJUSTMENT: mantiene il segno dell'input
    return quantity


# --- field resolvers: item ---
def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj["shelter_id"])


def get_current_quantity(obj, info):
    return items_data.get_current_quantity(obj["id"])


def get_is_below_threshold(obj, info):
    threshold = obj.get("minimum_threshold")
    if threshold is None:
        return False
    return items_data.get_current_quantity(obj["id"]) < threshold


def get_item_movements(obj, info, **kwargs):
    items = movements_data.get_movements_by_item(obj["id"])
    pagination = {
        "total_items": len(items),
        "total_pages": 1,
        "current_page": 0,
        "page_size": len(items),
    }
    return {"success": True, "items": items, "pagination": pagination}


def get_archived_by(obj, info):
    if not obj.get("archived_by_id"):
        return None
    return users_domain.get_user(obj["archived_by_id"])


# --- field resolvers: movement ---
def get_item(obj, info):
    return items_data.get_shelter_inventory_item(obj["item_id"])


def get_registered_by(obj, info):
    return users_domain.get_user(obj["registered_by_id"])


# --- helpers ---
def shelter_id_for_item(item_id):
    return items_data.get_shelter_inventory_item(item_id)["shelter_id"]


# --- business: item ---
def create_shelter_inventory_item(data, current_user_id):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter = shelters_domain.get_shelter(data.get("shelter_id"))
        if shelter is None:
            raise NotFoundError(f'no shelter found with id {data.get("shelter_id")}')
        item = items_data.create_shelter_inventory_item(data)
        initial = data.get("initial_quantity")
        if initial and initial > 0:
            movements_data.create_shelter_inventory_movement({
                "item_id": item["id"],
                "movement_type": "RESTOCK",
                "quantity": abs(initial),
                "registered_by_id": current_user_id,
                "notes": "initial stock",
            })
        return item
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_inventory_item(id, data):
    logger.domain(f"id: {id}\ndata: {stringify(data)}")
    try:
        clean = {k: v for k, v in data.items() if v is not None}
        return items_data.update_shelter_inventory_item(id, clean)
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_inventory_item(id, user_id):
    """Hard-delete only when the item has no movement history; otherwise the
    caller must archive it to preserve the ledger."""
    logger.domain(f"id: {id} remove")
    try:
        item = items_data.get_shelter_inventory_item(id)
        if items_data.count_movements(id) > 0:
            raise CannotDeleteWithHistoryError(
                "inventory item has movement history; archive it instead of deleting"
            )
        return damnatio_domain.delete_row(id, 'shelter_inventory_items', item, user_id)
    except Exception as e:
        logger.error(e)
        raise e


def archive_shelter_inventory_item(id, user_id):
    logger.domain(f"id: {id} archive by {user_id}")
    try:
        items_data.get_shelter_inventory_item(id)  # 404 if missing
        return items_data.archive_shelter_inventory_item(id, user_id)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_inventory_item(id):
    return items_data.get_shelter_inventory_item(id)


def get_paginated_items(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = _pagination(items_data, common_search)
        items = items_data.get_shelter_inventory_items(common_search)
        return (items, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def list_low_stock_items(shelter_id):
    logger.domain(f"shelter_id: {shelter_id}")
    try:
        items = items_data.get_items_by_shelter(shelter_id)
        low = [
            it for it in items
            if it.get("minimum_threshold") is not None
            and items_data.get_current_quantity(it["id"]) < it["minimum_threshold"]
        ]
        pagination = {
            "total_items": len(low),
            "total_pages": 1,
            "current_page": 0,
            "page_size": len(low),
        }
        return (low, pagination)
    except Exception as e:
        logger.error(e)
        raise e


# --- business: movement ---
def create_shelter_inventory_movement(data, current_user_id, allow_negative=False):
    """Record a stock movement. Blocks moves that would drive the running total
    below zero unless `allow_negative` (an authorized override) is set."""
    logger.domain(f"data: {stringify(data)}")
    try:
        item = items_data.get_shelter_inventory_item(data.get("item_id"))
        if item is None:
            raise NotFoundError(f'no inventory item found with id {data.get("item_id")}')
        signed = apply_sign(data["movement_type"], data["quantity"])
        if signed < 0 and not allow_negative:
            current = items_data.get_current_quantity(data["item_id"])
            if current + signed < 0:
                raise InsufficientStockError(
                    f"movement would drop stock below zero "
                    f"(current {current}, change {signed})"
                )
        payload = {
            "item_id": data["item_id"],
            "movement_type": data["movement_type"],
            "quantity": signed,
            "registered_by_id": current_user_id,
            "notes": data.get("notes"),
        }
        return movements_data.create_shelter_inventory_movement(payload)
    except Exception as e:
        logger.error(e)
        raise e


def get_paginated_movements(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = _pagination(movements_data, common_search)
        movements = movements_data.get_shelter_inventory_movements(common_search)
        return (movements, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def _pagination(data_module, common_search):
    total_items = data_module.get_total_items(common_search)
    page_size = common_search["pagination"]["page_size"]
    total_pages = ceil(total_items / page_size)
    current_page = common_search["pagination"]["page"]
    return {
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": current_page,
        "page_size": page_size,
    }
