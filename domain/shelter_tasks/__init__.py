from math import ceil
from datetime import datetime, timedelta

import repository.shelter_tasks as shelter_tasks_data
import repository.shelter_roles as shelter_roles_data
import domain.shelters as shelters_domain
import domain.shelter_pets as shelter_pets_domain
import domain.users as users_domain
import domain.shelter_people as shelter_people_domain
import domain.damnationes_memoriae as damnatio_domain
from api.errors import NotFoundError, BadRequest
from repository.shelter_tasks.models import TaskStatus
from domain.shelter_tasks import recurrence as rec
from utils.logger import logger, stringify
from utils.dates import utc_now

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


# --- field resolvers ---
def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj["shelter_id"])


def get_shelter_pet(obj, info):
    if not obj.get("shelter_pet_id"):
        return None
    return shelter_pets_domain.get_shelter_pet(obj["shelter_pet_id"])


def get_assignees(obj, info):
    ids = shelter_tasks_data.get_task_assignee_ids(obj["id"])
    return [users_domain.get_user(uid) for uid in ids]


def get_assignee_shelter_people(obj, info):
    ids = shelter_tasks_data.get_task_assignee_shelter_person_ids(obj["id"])
    return [shelter_people_domain.get_shelter_person(pid) for pid in ids]


def _assert_shelter_members(shelter_id, assignee_ids):
    """Every assignee must hold a role on this shelter (canile)."""
    for uid in dict.fromkeys(assignee_ids or []):
        if not shelter_roles_data.get_roles_for_user_on_shelter(uid, shelter_id):
            raise BadRequest(f"user {uid} is not a member of shelter {shelter_id}")


def _assert_shelter_people(shelter_id, shelter_person_ids):
    """Every shelter_person assignee (contact/volunteer without an account)
    must belong to this shelter."""
    for pid in dict.fromkeys(shelter_person_ids or []):
        person = shelter_people_domain.get_shelter_person(pid)
        if person is None or person["shelter_id"] != shelter_id:
            raise BadRequest(f"shelter_person {pid} does not belong to shelter {shelter_id}")


def get_completed_by(obj, info):
    if not obj.get("completed_by_id"):
        return None
    return users_domain.get_user(obj["completed_by_id"])


def get_skipped_by(obj, info):
    if not obj.get("skipped_by_id"):
        return None
    return users_domain.get_user(obj["skipped_by_id"])


def get_recurrence(obj, info):
    return rec.build(obj)


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
        if data.get("assignee_ids"):
            _assert_shelter_members(data.get("shelter_id"), data.get("assignee_ids"))
        if data.get("assignee_shelter_person_ids"):
            _assert_shelter_people(data.get("shelter_id"), data.get("assignee_shelter_person_ids"))
        data = rec.apply_to_data(dict(data))
        return shelter_tasks_data.create_shelter_task(data)
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_task(id, data):
    logger.domain(f"id: {id}\ndata: {stringify(data)}")
    try:
        data = dict(data)
        # assignee_ids/assignee_shelter_person_ids may legitimately be [] (clear
        # all) — keep them out of the None-stripping below and validate against
        # the task's own shelter.
        has_assignees = "assignee_ids" in data
        assignee_ids = data.pop("assignee_ids", None)
        has_shelter_people = "assignee_shelter_person_ids" in data
        shelter_person_ids = data.pop("assignee_shelter_person_ids", None)
        data = rec.apply_to_data(data)
        clean = {k: v for k, v in data.items() if v is not None}
        if has_assignees or has_shelter_people:
            task = shelter_tasks_data.get_shelter_task(id)
            if has_assignees:
                _assert_shelter_members(task["shelter_id"], assignee_ids)
                clean["assignee_ids"] = assignee_ids or []
            if has_shelter_people:
                _assert_shelter_people(task["shelter_id"], shelter_person_ids)
                clean["assignee_shelter_person_ids"] = shelter_person_ids or []
        return shelter_tasks_data.update_shelter_task(id, clean)
    except Exception as e:
        logger.error(e)
        raise e


def _assert_actionable_instance(task):
    """complete/skip act on task instances, never on recurring templates."""
    if task is None:
        raise NotFoundError("no shelter_task found")
    if task.get("is_recurring"):
        raise BadRequest("cannot complete/skip a recurring template; act on its instances")


def complete_shelter_task(id, user_id, notes=None):
    logger.domain(f"id: {id} complete by {user_id}")
    try:
        _assert_actionable_instance(shelter_tasks_data.get_shelter_task(id))
        payload = {
            "status": TaskStatus.COMPLETED.name,
            "completed_at": utc_now().strftime(DATE_FMT),
            "completed_by_id": user_id,
        }
        if notes is not None:
            payload["notes"] = notes
        return shelter_tasks_data.update_shelter_task(id, payload)
    except Exception as e:
        logger.error(e)
        raise e


def skip_shelter_task(id, user_id=None, reason=None):
    logger.domain(f"id: {id} skip by {user_id}")
    try:
        _assert_actionable_instance(shelter_tasks_data.get_shelter_task(id))
        payload = {
            "status": TaskStatus.SKIPPED.name,
            "skipped_at": utc_now().strftime(DATE_FMT),
            "skipped_by_id": user_id,
        }
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
def materialize_recurring_tasks(target_date=None):
    """Crea record PENDING per i template ricorrenti che ricorrono in target_date
    (default: oggi). All'ora indicata dalla ricorrenza. Idempotente via
    template_id. Ritorna il numero creato."""
    if target_date is None:
        target_date = utc_now().date()
    day_start = datetime(target_date.year, target_date.month, target_date.day)
    day_end = day_start + timedelta(days=1)
    logger.domain(f"materialize recurring tasks for {target_date}")
    created = 0
    try:
        for tpl in shelter_tasks_data.get_recurring_templates():
            if not rec.occurs_on(tpl, target_date):
                continue
            # idempotency: one instance per template per scheduled day
            if shelter_tasks_data.has_instance_on_date(tpl["id"], target_date):
                continue
            hour, minute = rec.rule_time(tpl)
            scheduled = datetime(
                target_date.year, target_date.month, target_date.day, hour, minute
            )
            row = shelter_tasks_data.create_task_instance({
                "shelter_id": tpl["shelter_id"],
                "shelter_pet_id": tpl.get("shelter_pet_id"),
                "shelter_box_id": tpl.get("shelter_box_id"),
                "task_type": tpl["task_type"],
                "area": tpl.get("area"),
                "status": TaskStatus.PENDING.name,
                "scheduled_at": scheduled.strftime(DATE_FMT),
                "scheduled_date": target_date.strftime("%Y-%m-%d"),
                "is_recurring": False,
                "template_id": tpl["id"],
                "notes": tpl.get("notes"),
            })
            if row is not None:
                # inherit the template's assignee set
                tpl_assignees = shelter_tasks_data.get_task_assignee_ids(tpl["id"])
                tpl_shelter_people = shelter_tasks_data.get_task_assignee_shelter_person_ids(tpl["id"])
                if tpl_assignees or tpl_shelter_people:
                    shelter_tasks_data.set_task_assignees(row["id"], tpl_assignees, tpl_shelter_people)
                created += 1
        logger.check(f"materialized {created} recurring shelter tasks")
        return created
    except Exception as e:
        logger.error(e)
        raise e


def get_operational_tasks(shelter_id, restrict_to_user_id=None):
    """Non-history tasks view: recurring templates + current-week tasks (see
    repository.shelter_tasks.get_operational_tasks for the exact rule)."""
    logger.domain(f"shelter_id: {shelter_id}")
    try:
        now = utc_now()
        day_start = datetime(now.year, now.month, now.day)
        week_start = day_start - timedelta(days=day_start.weekday())
        week_end = week_start + timedelta(days=7)
        tasks = shelter_tasks_data.get_operational_tasks(
            shelter_id, week_start, week_end, restrict_to_user_id)
        pagination = {
            "total_items": len(tasks),
            "total_pages": 1,
            "current_page": 0,
            "page_size": len(tasks),
        }
        return (tasks, pagination)
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
