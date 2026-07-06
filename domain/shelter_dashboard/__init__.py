from datetime import datetime, timedelta

import repository.shelter_walks as walks_data
import repository.shelter_tasks as tasks_data
import repository.shelter_maps as maps_data
import repository.shelter_boxes as boxes_data
import repository.shelter_box_occupancies as occ_data
import repository.shelter_pets as pets_data
import domain.shelter_inventory as inventory_domain
from utils.logger import logger


def _box_stats(shelter_id):
    total = free = occupied = full = out_of_service = 0
    for shelter_map in maps_data.get_maps_by_shelter(shelter_id):
        for box in boxes_data.get_boxes_by_map(shelter_map["id"]):
            total += 1
            if box.get("is_out_of_service"):
                out_of_service += 1
                continue
            count = occ_data.count_active_for_box(box["id"])
            capacity = box.get("capacity") or 1
            if count <= 0:
                free += 1
            elif count >= capacity:
                full += 1
            else:
                occupied += 1
    return total, free, occupied, full, out_of_service


def get_operational_dashboard(shelter_id):
    logger.domain(f"operational dashboard for shelter {shelter_id}")
    try:
        now = datetime.today()
        day_start = datetime(now.year, now.month, now.day)
        day_end = day_start + timedelta(days=1)

        boxes_total, boxes_free, boxes_occupied, boxes_full, boxes_oos = _box_stats(shelter_id)
        low_stock, _ = inventory_domain.list_low_stock_items(shelter_id)

        return {
            "shelter_id": shelter_id,
            "walks_completed_today": walks_data.count_completed_between(shelter_id, day_start, day_end),
            "walks_planned_today": walks_data.count_planned_between(shelter_id, day_start, day_end),
            "pets_needing_walk": len(walks_data.get_pets_needing_walk(shelter_id, 24)),
            "tasks_pending": tasks_data.count_by_status(shelter_id, ["PENDING", "IN_PROGRESS"]),
            "tasks_overdue": tasks_data.count_overdue(shelter_id, now),
            "tasks_completed_today": tasks_data.count_completed_between(shelter_id, day_start, day_end),
            "boxes_total": boxes_total,
            "boxes_free": boxes_free,
            "boxes_occupied": boxes_occupied,
            "boxes_full": boxes_full,
            "boxes_out_of_service": boxes_oos,
            "pets_total": pets_data.count_in_shelter(shelter_id),
            "low_stock_count": len(low_stock),
        }
    except Exception as e:
        logger.error(e)
        raise e
