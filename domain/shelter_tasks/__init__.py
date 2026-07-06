from math import ceil
from datetime import datetime, timedelta

import repository.shelter_tasks as shelter_tasks_data
import domain.shelters as shelters_domain
import domain.shelter_pets as shelter_pets_domain
import domain.users as users_domain
import domain.damnationes_memoriae as damnatio_domain
from api.errors import NotFoundError
from repository.shelter_tasks.models import TaskStatus
from utils.logger import logger, stringify

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


# --- field resolvers ---
def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj["shelter_id"])


def get_shelter_pet(obj, info):
    if not obj.get("shelter_pet_id"):
        return None
    return shelter_pets_domain.get_shelter_pet(obj["shelter_pet_id"])


def get_assigned_to(obj, info):
    if not obj.get("assigned_to_id"):
        return None
    return users_domain.get_user(obj["assigned_to_id"])


def get_completed_by(obj, info):
    if not obj.get("completed_by_id"):
        return None
    return users_domain.get_user(obj["completed_by_id"])


# --- business ---
def create_shelter_task(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter = shelters_domain.get_shelter(data.get("shelter_id"))
        if shelter is None:
            raise NotFoundError(f'no shelter found with id {data.get("shelter_id")}')
        if data.get("shelter_pet_id"):
            pet = shelter_pets_domain.get_shelter_pet(data.get("shelter_pet_id"))
            if pet is None:
                raise NotFoundError(f'no shelter_pet found with id {data.get("shelter_pet_id")}')
        return shelter_tasks_data.create_shelter_task(data)
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_task(id, data):
    logger.domain(f"id: {id}\ndata: {stringify(data)}")
    try:
        clean = {k: v for k, v in data.items() if v is not None}
        return shelter_tasks_data.update_shelter_task(id, clean)
    except Exception as e:
        logger.error(e)
        raise e


def complete_shelter_task(id, user_id, notes=None):
    logger.domain(f"id: {id} complete by {user_id}")
    try:
        payload = {
            "status": TaskStatus.COMPLETED.name,
            "completed_at": datetime.today().strftime(DATE_FMT),
            "completed_by_id": user_id,
        }
        if notes is not None:
            payload["notes"] = notes
        return shelter_tasks_data.update_shelter_task(id, payload)
    except Exception as e:
        logger.error(e)
        raise e


def skip_shelter_task(id, reason=None):
    logger.domain(f"id: {id} skip")
    try:
        payload = {"status": TaskStatus.SKIPPED.name}
        if reason is not None:
            payload["notes"] = reason
        return shelter_tasks_data.update_shelter_task(id, payload)
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_task(id, user_id):
    logger.domain(f"id: {id} remove")
    try:
        shelter_task = shelter_tasks_data.get_shelter_task(id)
        memoriae_id = damnatio_domain.delete_row(id, 'shelter_tasks', shelter_task, user_id)
        return memoriae_id
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_task(id):
    return shelter_tasks_data.get_shelter_task(id)


# --- ricorrenze (materializzazione da cron) ---
WEEKDAYS = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


def _occurs_on(rule, day):
    """Supporta 'DAILY' e 'WEEKLY:MON,WED,FRI'. Altri formati (cron) ignorati."""
    if not rule:
        return False
    rule = rule.strip().upper()
    if rule == "DAILY":
        return True
    if rule.startswith("WEEKLY:"):
        days = rule.split(":", 1)[1].split(",")
        wanted = [WEEKDAYS[d.strip()] for d in days if d.strip() in WEEKDAYS]
        return day.weekday() in wanted
    return False


def materialize_recurring_tasks(target_date=None):
    """Crea record PENDING per i template ricorrenti che ricorrono in target_date
    (default: domani). Idempotente via template_id. Ritorna il numero creato."""
    if target_date is None:
        target_date = (datetime.today() + timedelta(days=1)).date()
    day_start = datetime(target_date.year, target_date.month, target_date.day)
    day_end = day_start + timedelta(days=1)
    scheduled_iso = day_start.strftime(DATE_FMT)
    logger.domain(f"materialize recurring tasks for {target_date}")
    created = 0
    try:
        for tpl in shelter_tasks_data.get_recurring_templates():
            if not _occurs_on(tpl.get("recurrence_rule"), target_date):
                continue
            if shelter_tasks_data.has_occurrence_on(tpl["id"], day_start, day_end):
                continue
            shelter_tasks_data.create_shelter_task({
                "shelter_id": tpl["shelter_id"],
                "shelter_pet_id": tpl.get("shelter_pet_id"),
                "shelter_box_id": tpl.get("shelter_box_id"),
                "task_type": tpl["task_type"],
                "area": tpl.get("area"),
                "status": TaskStatus.PENDING.name,
                "assigned_to_id": tpl.get("assigned_to_id"),
                "scheduled_at": scheduled_iso,
                "is_recurring": False,
                "template_id": tpl["id"],
                "notes": tpl.get("notes"),
            })
            created += 1
        logger.check(f"materialized {created} recurring shelter tasks")
        return created
    except Exception as e:
        logger.error(e)
        raise e


def get_paginated_shelter_tasks(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        tasks = shelter_tasks_data.get_shelter_tasks(common_search)
        return (tasks, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    try:
        total_items = shelter_tasks_data.get_total_items(common_search)
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
