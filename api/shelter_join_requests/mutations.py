from ariadne import convert_kwargs_to_snake_case

import domain.shelter_join_requests as join_requests_domain
from api.middlewares import auth_middleware
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger


def _ok(join_request=None):
    return {"success": True, "shelter_join_request": join_request}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def apply_to_shelter_as_volunteer_resolver(obj, info, shelter_id, message=None):
    logger.api(f"apply as volunteer to {shelter_id}")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(join_requests_domain.apply_as_volunteer(shelter_id, me.get("id"), message))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def approve_shelter_join_request_resolver(obj, info, id):
    logger.api(f"approve shelter join request {id}")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(join_requests_domain.approve_join_request(id, me.get("id")))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def reject_shelter_join_request_resolver(obj, info, id):
    logger.api(f"reject shelter join request {id}")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(join_requests_domain.reject_join_request(id, me.get("id")))
    except Exception as e:
        return _err(e, info)
