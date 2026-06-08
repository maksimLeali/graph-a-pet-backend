from ariadne import ObjectType, convert_kwargs_to_snake_case
import domain.shelter_roles as shelter_roles_domain
import domain.shelter_pets as shelter_pets_domain
from api.errors import error_pagination
from utils import format_common_search
from utils.logger import logger, stringify

shelter = ObjectType("Shelter")


def _inject_shelter_filter(common_search, shelter_id):
    common_search['filters']['and'] = {
        **(common_search['filters'].get('and') if common_search['filters'].get('and') is not None else {}),
        **{
            'fixed': {
                **(common_search['filters'].get('and').get('fixed')
                   if common_search['filters'].get('and') is not None
                   and common_search['filters'].get('and').get('fixed') is not None else {}),
                **{'shelter_id': shelter_id},
            }
        }
    }
    return common_search


@shelter.field('roles')
@convert_kwargs_to_snake_case
def shelter_roles_resolver(obj, info, common_search):
    common_search = _inject_shelter_filter(format_common_search(common_search), obj['id'])
    logger.api(
        f"shelter_id: {obj['id']}\n"
        f"common_search: {stringify(common_search)}"
    )
    try:
        roles, pagination = shelter_roles_domain.get_paginated_shelter_roles(common_search)
        return {
            "items": roles,
            "pagination": pagination,
            "success": True,
        }
    except Exception as e:
        logger.error(e)
        return {
            "items": [],
            "pagination": error_pagination,
            "success": False,
        }


@shelter.field('pets')
@convert_kwargs_to_snake_case
def shelter_pets_resolver(obj, info, common_search):
    common_search = _inject_shelter_filter(format_common_search(common_search), obj['id'])
    logger.api(
        f"shelter_id: {obj['id']}\n"
        f"common_search: {stringify(common_search)}"
    )
    try:
        pets, pagination = shelter_pets_domain.get_paginated_shelter_pets(common_search)
        return {
            "items": pets,
            "pagination": pagination,
            "success": True,
        }
    except Exception as e:
        logger.error(e)
        return {
            "items": [],
            "pagination": error_pagination,
            "success": False,
        }
