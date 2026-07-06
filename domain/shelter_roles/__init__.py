import repository.shelter_roles as shelter_roles_data
import domain.users as users_domain
import domain.shelters as shelters_domain
from api.errors import BadRequest, NotFoundError
import domain.damnationes_memoriae as damnatio_domain
from utils.logger import logger, stringify
from math import ceil
import pydash as py_


SHELTER_ROLE_UPDATE_FIELDS = ["role"]


def get_user(obj, info):
    return users_domain.get_user(obj['user_id'])


def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj['shelter_id'])


def create_shelter_role(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        user = users_domain.get_user(data.get('user_id'))
        if user is None:
            raise NotFoundError(f'no user found with id {data.get("user_id")}')
        shelter = shelters_domain.get_shelter(data.get('shelter_id'))
        if shelter is None:
            raise NotFoundError(f'no shelter found with id {data.get("shelter_id")}')
        if data.get('role') is None:
            raise BadRequest('missing role')
        return shelter_roles_data.create_shelter_role(data)
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_role(id, data):
    logger.domain(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        shelter_role = shelter_roles_data.update_shelter_role(id, py_.pick(data, SHELTER_ROLE_UPDATE_FIELDS))
        logger.check(f"shelter_role: {stringify(shelter_role)}")
        return shelter_role
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_role(id, user_id):
    logger.domain(f"id {id} remove")
    try:
        shelter_role = shelter_roles_data.get_shelter_role(id)
        memoriae_id = damnatio_domain.delete_row(id, 'shelter_roles', shelter_role, user_id)
        return memoriae_id
    except Exception as e:
        logger.error(e)
        raise e


def get_paginated_shelter_roles(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        shelter_roles = get_shelter_roles(common_search)
        return (shelter_roles, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_roles(common_search):
    try:
        return shelter_roles_data.get_shelter_roles(common_search)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_role(id):
    return shelter_roles_data.get_shelter_role(id)


def get_filtered_shelter_roles(filters):
    return shelter_roles_data.get_filtered_shelter_roles(filters)


def get_user_roles_on_shelter(user_id, shelter_id):
    return shelter_roles_data.get_roles_for_user_on_shelter(user_id, shelter_id)


def get_pagination(common_search):
    try:
        total_items = shelter_roles_data.get_total_items(common_search)
        page_size = common_search['pagination']['page_size']
        total_pages = ceil(total_items / page_size)
        current_page = common_search['pagination']['page']
        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error(e)
        raise e
