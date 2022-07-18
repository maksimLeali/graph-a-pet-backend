from ariadne import convert_kwargs_to_snake_case
import domain.treatments as treatments_domain
from libs.logger import logger, stringify
from libs.utils import format_common_search
from api.errors import InternalError, error_pagination, format_error
from api.middlewares import min_role, RoleLevel


@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def list_treatments_resolver(obj, info, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    try:
        common_search = format_common_search(common_search)
        treatments, pagination = treatments_domain.get_paginated_treatments(common_search)
        payload = {
            "success": True,
            "items": treatments,
            "pagination": pagination,
        }
        logger.check(f"treatments found: {len(treatments)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']) ,
            "items": [],
            "pagination": error_pagination 
        }
    return payload


@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def get_treatment_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        treatment = treatments_domain.get_treatment(id)
        payload = {
            "success": True,
            "treatment": treatment
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "treatment":None, 
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return payload
