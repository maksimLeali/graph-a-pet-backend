from math import ceil
from datetime import datetime, timedelta

import repository.shelter_walks as shelter_walks_data
import domain.shelter_pets as shelter_pets_domain
import domain.users as users_domain
import domain.shelter_people as shelter_people_domain
import domain.damnationes_memoriae as damnatio_domain
from api.errors import NotFoundError, BadRequest
from repository.shelter_walks.models import ShelterWalkStatus
from utils import difference_in_minutes
from utils.logger import logger, stringify
from utils.dates import utc_now

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


# --- field resolvers ---
def get_shelter_pet(obj, info):
    return shelter_pets_domain.get_shelter_pet(obj["shelter_pet_id"])


def get_walker(obj, info):
    if not obj.get("walker_id"):
        return None
    return users_domain.get_user(obj["walker_id"])


def get_walker_shelter_person(obj, info):
    if not obj.get("shelter_person_id"):
        return None
    return shelter_people_domain.get_shelter_person(obj["shelter_person_id"])


# --- helpers ---
def shelter_id_for_walk(id):
    walk = shelter_walks_data.get_shelter_walk(id)
    return shelter_id_for_shelter_pet(walk["shelter_pet_id"])


def shelter_id_for_shelter_pet(shelter_pet_id):
    sp = shelter_pets_domain.get_shelter_pet(shelter_pet_id)
    if sp is None:
        raise NotFoundError(f"no shelter_pet found with id {shelter_pet_id}")
    return sp["shelter_id"]


# --- business ---
def create_shelter_walk(data, current_user_id):
    logger.domain(f"data: {stringify(data)}")
    try:
        sp = shelter_pets_domain.get_shelter_pet(data.get("shelter_pet_id"))
        if sp is None:
            raise NotFoundError(f'no shelter_pet found with id {data.get("shelter_pet_id")}')
        payload = dict(data)
        if data.get("shelter_person_id"):
            # walker is a shelter contact/volunteer without an app account
            person = shelter_people_domain.get_shelter_person(data["shelter_person_id"])
            if person["shelter_id"] != sp["shelter_id"]:
                raise BadRequest("shelter_person does not belong to this shelter")
            payload["walker_id"] = None
        else:
            payload["walker_id"] = data.get("walker_id") or current_user_id
            payload["shelter_person_id"] = None
        return shelter_walks_data.create_shelter_walk(payload)
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_walk(id, data):
    logger.domain(f"id: {id}\ndata: {stringify(data)}")
    try:
        clean = {k: v for k, v in data.items() if v is not None}
        return shelter_walks_data.update_shelter_walk(id, clean)
    except Exception as e:
        logger.error(e)
        raise e


def start_shelter_walk(id):
    logger.domain(f"id: {id} start")
    try:
        return shelter_walks_data.update_shelter_walk(id, {
            "status": ShelterWalkStatus.IN_PROGRESS.name,
            "started_at": utc_now().strftime(DATE_FMT),
        })
    except Exception as e:
        logger.error(e)
        raise e


def complete_shelter_walk(id, notes=None):
    logger.domain(f"id: {id} complete")
    try:
        walk = shelter_walks_data.get_shelter_walk(id)
        ended = utc_now().strftime(DATE_FMT)
        payload = {
            "status": ShelterWalkStatus.COMPLETED.name,
            "ended_at": ended,
        }
        if walk.get("started_at"):
            payload["duration_minutes"] = int(round(difference_in_minutes(walk["started_at"], ended)))
        if notes is not None:
            payload["notes"] = notes
        return shelter_walks_data.update_shelter_walk(id, payload)
    except Exception as e:
        logger.error(e)
        raise e


def cancel_shelter_walk(id, reason=None):
    logger.domain(f"id: {id} cancel")
    try:
        payload = {
            "status": ShelterWalkStatus.CANCELLED.name,
            "cancelled_at": utc_now().strftime(DATE_FMT),
        }
        if reason is not None:
            payload["notes"] = reason
        return shelter_walks_data.update_shelter_walk(id, payload)
    except Exception as e:
        logger.error(e)
        raise e


def set_manual_duration(id, duration_minutes):
    """Overrides duration_minutes directly and clears started_at/ended_at:
    their absence *is* the "manual" flag the FE renders (no separate column)."""
    logger.domain(f"id: {id} duration_minutes: {duration_minutes}")
    try:
        return shelter_walks_data.update_shelter_walk(id, {
            "duration_minutes": duration_minutes,
            "started_at": None,
            "ended_at": None,
        })
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_walk(id, user_id):
    logger.domain(f"id: {id} remove")
    try:
        walk = shelter_walks_data.get_shelter_walk(id)
        memoriae_id = damnatio_domain.delete_row(id, 'shelter_walks', walk, user_id)
        return memoriae_id
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_walk(id):
    return shelter_walks_data.get_shelter_walk(id)


def get_paginated_shelter_walks(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        walks = shelter_walks_data.get_shelter_walks(common_search)
        return (walks, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_operational_walks(shelter_id, restrict_to_user_id=None):
    """Non-history walks view: open walks + walks closed today (see
    repository.shelter_walks.get_operational_walks for the exact rule)."""
    logger.domain(f"shelter_id: {shelter_id}")
    try:
        now = utc_now()
        day_start = datetime(now.year, now.month, now.day)
        day_end = day_start + timedelta(days=1)
        walks = shelter_walks_data.get_operational_walks(
            shelter_id, day_start, day_end, restrict_to_user_id)
        pagination = {
            "total_items": len(walks),
            "total_pages": 1,
            "current_page": 0,
            "page_size": len(walks),
        }
        return (walks, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_pets_needing_walk(shelter_id, hours=24, restrict_to_user_id=None):
    logger.domain(f"shelter_id: {shelter_id} hours: {hours}")
    try:
        pets = shelter_walks_data.get_pets_needing_walk(shelter_id, hours, restrict_to_user_id)
        pagination = {
            "total_items": len(pets),
            "total_pages": 1,
            "current_page": 0,
            "page_size": len(pets),
        }
        return (pets, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    try:
        total_items = shelter_walks_data.get_total_items(common_search)
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
