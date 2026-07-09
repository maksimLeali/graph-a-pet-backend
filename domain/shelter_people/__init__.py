from math import ceil

import repository.shelter_people as people_data
import domain.shelters as shelters_domain
import domain.users as users_domain
from api.errors import NotFoundError, BadRequest
from utils.logger import logger, stringify

UPDATE_FIELDS = ["first_name", "last_name", "email", "phone", "status", "source", "notes"]


# --- field resolvers ---
def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj["shelter_id"])


def get_user(obj, info):
    if not obj.get("user_id"):
        return None
    return users_domain.get_user(obj["user_id"])


def get_created_by(obj, info):
    if not obj.get("created_by_id"):
        return None
    return users_domain.get_user(obj["created_by_id"])


def get_archived_by(obj, info):
    if not obj.get("archived_by_id"):
        return None
    return users_domain.get_user(obj["archived_by_id"])


# --- helpers ---
def shelter_id_for_person(id):
    return people_data.get_shelter_person(id)["shelter_id"]


def _has_identifier(data):
    return any(data.get(k) for k in ("first_name", "last_name", "email", "phone"))


def _inject_shelter_filter(common_search, shelter_id):
    filters = common_search.setdefault("filters", {})
    grp = filters.setdefault("and", {})
    fixed = grp.setdefault("fixed", {})
    fixed["shelter_id"] = shelter_id
    return common_search


# --- business ---
def create_shelter_person(data, current_user_id):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter = shelters_domain.get_shelter(data.get("shelter_id"))
        if shelter is None:
            raise NotFoundError(f'no shelter found with id {data.get("shelter_id")}')
        if not _has_identifier(data):
            raise BadRequest("at least one of name, phone or email is required")
        payload = dict(data)
        payload["created_by_id"] = current_user_id
        # never fabricate accounts: a link to a real user means ACTIVE_USER
        if payload.get("user_id"):
            user = users_domain.get_user(payload["user_id"])
            if user is None:
                raise NotFoundError(f'no user found with id {payload["user_id"]}')
            payload["status"] = "ACTIVE_USER"
        elif not payload.get("status"):
            payload["status"] = "VISITOR"
        return people_data.create_shelter_person(payload)
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_person(id, data):
    logger.domain(f"id: {id}\ndata: {stringify(data)}")
    try:
        clean = {k: v for k, v in data.items() if k in UPDATE_FIELDS and v is not None}
        return people_data.update_shelter_person(id, clean)
    except Exception as e:
        logger.error(e)
        raise e


def archive_shelter_person(id, user_id):
    logger.domain(f"id: {id} archive")
    return people_data.archive_shelter_person(id, user_id)


def link_shelter_person_to_user(person_id, user_id):
    logger.domain(f"link person {person_id} to user {user_id}")
    try:
        person = people_data.get_shelter_person(person_id)
        if person is None:
            raise NotFoundError(f"no shelter_person found with id: {person_id}")
        user = users_domain.get_user(user_id)
        if user is None:
            raise NotFoundError(f"no user found with id {user_id}")
        return people_data.update_shelter_person(person_id, {
            "user_id": user_id,
            "status": "ACTIVE_USER",
        })
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_person(id):
    return people_data.get_shelter_person(id)


def get_paginated_shelter_people(shelter_id, common_search):
    logger.domain(f"shelter_id: {shelter_id} common_search: {stringify(common_search)}")
    try:
        _inject_shelter_filter(common_search, shelter_id)
        people = people_data.get_shelter_people(common_search)
        pagination = get_pagination(common_search)
        return people, pagination
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    total_items = people_data.get_total_items(common_search)
    page_size = common_search["pagination"]["page_size"]
    total_pages = ceil(total_items / page_size) if page_size else 0
    return {
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": common_search["pagination"]["page"],
        "page_size": page_size,
    }
