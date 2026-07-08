from datetime import datetime, timedelta

import repository.shelter_walks as walks_data
import repository.shelter_tasks as tasks_data
import repository.shelter_maps as maps_data
import repository.shelter_boxes as boxes_data
import repository.shelter_box_occupancies as occ_data
import repository.shelter_pets as pets_data
import repository.shelters as shelters_data
import repository.shelter_dashboard_snapshots as snapshots_data
import domain.shelter_inventory as inventory_domain
from utils.logger import logger


def _box_stats(shelter_id):
    total = free = occupied = full = out_of_service = pets_in_box = 0
    for shelter_map in maps_data.get_maps_by_shelter(shelter_id):
        for box in boxes_data.get_boxes_by_map(shelter_map["id"]):
            total += 1
            count = occ_data.count_active_for_box(box["id"])
            pets_in_box += count  # un pet sta al più in un box
            if box.get("is_out_of_service"):
                out_of_service += 1
                continue
            capacity = box.get("capacity") or 1
            if count <= 0:
                free += 1
            elif count >= capacity:
                full += 1
            else:
                occupied += 1
    return total, free, occupied, full, out_of_service, pets_in_box


def get_operational_dashboard(shelter_id):
    logger.domain(f"operational dashboard for shelter {shelter_id}")
    try:
        now = datetime.today()
        day_start = datetime(now.year, now.month, now.day)
        day_end = day_start + timedelta(days=1)
        week_start = day_start - timedelta(days=day_start.weekday())
        week_end = week_start + timedelta(days=7)

        boxes_total, boxes_free, boxes_occupied, boxes_full, boxes_oos, pets_in_box = _box_stats(shelter_id)
        low_stock, _ = inventory_domain.list_low_stock_items(shelter_id)
        pets_total = pets_data.count_in_shelter(shelter_id)

        return {
            "shelter_id": shelter_id,
            "walks_completed_today": walks_data.count_completed_between(shelter_id, day_start, day_end),
            "walks_planned_today": walks_data.count_planned_between(shelter_id, day_start, day_end),
            "pets_needing_walk": len(walks_data.get_pets_needing_walk(shelter_id, 24)),
            "tasks_pending": tasks_data.count_by_status(shelter_id, ["PENDING", "IN_PROGRESS"]),
            "tasks_overdue": tasks_data.count_overdue(shelter_id, now),
            "tasks_completed_today": tasks_data.count_completed_between(shelter_id, day_start, day_end),
            "tasks_total": tasks_data.count_all(shelter_id),
            "tasks_recurring": tasks_data.count_recurring(shelter_id),
            "tasks_due_this_week": tasks_data.count_due_between(shelter_id, week_start, week_end),
            "boxes_total": boxes_total,
            "boxes_free": boxes_free,
            "boxes_occupied": boxes_occupied,
            "boxes_full": boxes_full,
            "boxes_out_of_service": boxes_oos,
            "pets_total": pets_total,
            "pets_without_box": max(0, pets_total - pets_in_box),
            "low_stock_count": len(low_stock),
        }
    except Exception as e:
        logger.error(e)
        raise e


def snapshot_all_shelters(target_date=None):
    """Storicizza i KPI operativi di ogni shelter per target_date (default oggi).
    Idempotente per (shelter, giorno). Ritorna il numero di snapshot salvati."""
    if target_date is None:
        target_date = datetime.today().date()
    logger.domain(f"snapshot KPI shelters for {target_date}")
    saved = 0
    for shelter in shelters_data.get_all_shelters():
        try:
            kpis = get_operational_dashboard(shelter.id)
            snapshots_data.upsert_snapshot(shelter.id, target_date, kpis)
            saved += 1
        except Exception as e:
            logger.error(e)  # non bloccare gli altri shelter
    logger.check(f"saved {saved} KPI snapshots")
    return saved


def get_kpi_history(shelter_id, days=30):
    logger.domain(f"kpi history shelter {shelter_id} days {days}")
    try:
        to_date = datetime.today().date()
        from_date = to_date - timedelta(days=max(1, days) - 1)
        return snapshots_data.get_history(shelter_id, from_date, to_date)
    except Exception as e:
        logger.error(e)
        raise e
