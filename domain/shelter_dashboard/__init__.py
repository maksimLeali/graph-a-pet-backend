from datetime import datetime, timedelta

import repository.shelter_walks as walks_data
import repository.shelter_tasks as tasks_data
import repository.shelter_maps as maps_data
import repository.shelter_boxes as boxes_data
import repository.shelter_box_occupancies as occ_data
import repository.shelter_pets as pets_data
import repository.shelters as shelters_data
import repository.shelter_dashboard_snapshots as snapshots_data
import repository.shelter_roles as shelter_roles_data
import repository.shelter_inventory_items as inventory_items_data
import domain.shelter_inventory as inventory_domain
import domain.shelter_boxes as boxes_domain
import domain.shelters as shelters_domain
import domain.pets as pets_domain
from utils.logger import logger

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
MANAGER_LEVEL_ROLES = {"MANAGER", "OWNER"}


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.strptime(value, DATE_FMT)


def _box_stats(shelter_id):
    stats = {
        "total": 0, "available": 0, "occupied": 0, "full": 0,
        "out_of_service": 0, "needs_cleaning": 0,
        "pets_in_box": 0, "capacity_in_service": 0,
    }
    for shelter_map in maps_data.get_maps_by_shelter(shelter_id):
        for box in boxes_data.get_boxes_by_map(shelter_map["id"]):
            stats["total"] += 1
            count = occ_data.count_active_for_box(box["id"])
            stats["pets_in_box"] += count  # a pet is in at most one box
            if box.get("is_out_of_service"):
                stats["out_of_service"] += 1
                continue
            capacity = box.get("capacity") or 1
            stats["capacity_in_service"] += capacity
            if count >= capacity:
                stats["full"] += 1
            elif count > 0:
                stats["occupied"] += 1
            elif boxes_domain._needs_cleaning(box):
                stats["needs_cleaning"] += 1
            else:
                stats["available"] += 1
    return stats


def get_operational_dashboard(shelter_id):
    logger.domain(f"operational dashboard for shelter {shelter_id}")
    try:
        now = datetime.today()
        day_start = datetime(now.year, now.month, now.day)
        day_end = day_start + timedelta(days=1)
        week_start = day_start - timedelta(days=day_start.weekday())
        week_end = week_start + timedelta(days=7)

        bs = _box_stats(shelter_id)
        pets_in_box = bs["pets_in_box"]
        low_stock, _ = inventory_domain.list_low_stock_items(shelter_id)
        pets_total = pets_data.count_in_shelter(shelter_id)
        occupancy_rate = (
            round(pets_in_box / bs["capacity_in_service"], 4)
            if bs["capacity_in_service"] > 0 else 0.0
        )

        return {
            "shelter_id": shelter_id,
            "walks_completed_today": walks_data.count_completed_between(shelter_id, day_start, day_end),
            "walks_planned_today": walks_data.count_planned_between(shelter_id, day_start, day_end),
            "walks_in_progress": walks_data.count_in_progress(shelter_id),
            "pets_needing_walk": len(walks_data.get_pets_needing_walk(shelter_id, 24)),
            "tasks_pending": tasks_data.count_by_status(shelter_id, ["PENDING", "IN_PROGRESS"]),
            "tasks_overdue": tasks_data.count_overdue(shelter_id, now),
            "tasks_completed_today": tasks_data.count_completed_between(shelter_id, day_start, day_end),
            "tasks_skipped_today": tasks_data.count_skipped_between(shelter_id, day_start, day_end),
            "tasks_total": tasks_data.count_all(shelter_id),
            "tasks_recurring": tasks_data.count_recurring(shelter_id),
            "tasks_due_this_week": tasks_data.count_due_between(shelter_id, week_start, week_end),
            "boxes_total": bs["total"],
            # boxes_free kept for backward-compat; boxes_available is the new name
            "boxes_free": bs["available"],
            "boxes_available": bs["available"],
            "boxes_occupied": bs["occupied"],
            "boxes_full": bs["full"],
            "boxes_out_of_service": bs["out_of_service"],
            "boxes_needing_cleaning": bs["needs_cleaning"],
            "occupancy_rate": occupancy_rate,
            "pets_total": pets_total,
            "pets_without_box": max(0, pets_total - pets_in_box),
            "low_stock_count": len(low_stock),
            "low_stock_items": low_stock,
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


def _shelter_name(shelter_id, cache):
    if shelter_id not in cache:
        shelter = shelters_domain.get_shelter(shelter_id)
        cache[shelter_id] = shelter["name"] if shelter else shelter_id
    return cache[shelter_id]


def get_my_shelter_dashboard(user_id, date_from, date_to, is_global_admin=False):
    """Cross-shelter 'what do I have to do' view: tasks/walks assigned to
    user_id, and (for MANAGER+/OWNER members) low/out-of-stock inventory,
    across every shelter/workspace the user belongs to."""
    logger.domain(f"user_id: {user_id} date_from: {date_from} date_to: {date_to}")
    try:
        start = _parse_dt(date_from)
        end = _parse_dt(date_to)
        now = datetime.today()
        day_start = datetime(now.year, now.month, now.day)
        day_end = day_start + timedelta(days=1)
        # tasks use the shelter/app week convention (Monday-Sunday), same as
        # get_operational_dashboard's tasks_due_this_week — not the rolling
        # date_from/date_to window used for walks.
        week_start = day_start - timedelta(days=day_start.weekday())
        week_end = week_start + timedelta(days=7)
        shelter_name_cache = {}

        my_roles = shelter_roles_data.get_roles_for_user(user_id)
        roles_by_shelter = {}
        for r in my_roles:
            roles_by_shelter.setdefault(r["shelter_id"], set()).add(r["role"])
        manager_shelter_ids = [
            sid for sid, roles in roles_by_shelter.items()
            if is_global_admin or (roles & MANAGER_LEVEL_ROLES)
        ]

        # --- tasks assigned to me (current week only) ---
        tasks = []
        overdue_task_count = 0
        for t in tasks_data.get_tasks_assigned_to_user(user_id, week_start, week_end):
            is_overdue = (
                t["status"] in ("PENDING", "IN_PROGRESS")
                and bool(t.get("scheduled_at"))
                and _parse_dt(t["scheduled_at"]) < now
            )
            if is_overdue:
                overdue_task_count += 1
            tasks.append({
                "id": t["id"],
                "shelter_id": t["shelter_id"],
                "shelter_name": _shelter_name(t["shelter_id"], shelter_name_cache),
                "task_type": t["task_type"],
                "area": t.get("area"),
                "status": t["status"],
                "is_overdue": is_overdue,
                "scheduled_at": t.get("scheduled_at"),
                "action_url": f"/shelters/detail/{t['shelter_id']}/tasks/{t['id']}",
            })

        # --- walks assigned to me ---
        walks = []
        in_progress_walk_count = 0
        for w in walks_data.get_walks_assigned_to_user(user_id, start, end, day_start, day_end):
            shelter_pet = pets_data.get_shelter_pet(w["shelter_pet_id"])
            shelter_id = shelter_pet["shelter_id"] if shelter_pet else None
            pet = pets_domain.get_pet(shelter_pet["pet_id"]) if shelter_pet else None
            if w["status"] == "IN_PROGRESS":
                in_progress_walk_count += 1
            walks.append({
                "id": w["id"],
                "shelter_id": shelter_id,
                "shelter_name": _shelter_name(shelter_id, shelter_name_cache) if shelter_id else "",
                "pet_name": pet["name"] if pet else "",
                "status": w["status"],
                "scheduled_at": w.get("scheduled_at"),
                "action_url": f"/shelters/detail/{shelter_id}/walks/{w['id']}" if shelter_id else "",
            })

        # --- inventory alerts (MANAGER+/OWNER shelters only) ---
        inventory_alerts = []
        low_stock_count = 0
        out_of_stock_count = 0
        for sid in manager_shelter_ids:
            low_items, _ = inventory_domain.list_low_stock_items(sid)
            for it in low_items:
                qty = inventory_items_data.get_current_quantity(it["id"])
                status = "OUT_OF_STOCK" if qty <= 0 else "LOW_STOCK"
                if status == "OUT_OF_STOCK":
                    out_of_stock_count += 1
                else:
                    low_stock_count += 1
                inventory_alerts.append({
                    "id": it["id"],
                    "shelter_id": sid,
                    "shelter_name": _shelter_name(sid, shelter_name_cache),
                    "name": it["name"],
                    "current_quantity": qty,
                    "minimum_threshold": it.get("minimum_threshold"),
                    "status": status,
                    "action_url": f"/shelters/detail/{sid}/inventory/{it['id']}/edit",
                })

        return {
            "task_count": len(tasks),
            "overdue_task_count": overdue_task_count,
            "walk_count": len(walks),
            "in_progress_walk_count": in_progress_walk_count,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "tasks": tasks,
            "walks": walks,
            "inventory_alerts": inventory_alerts,
        }
    except Exception as e:
        logger.error(e)
        raise e
