from ariadne import convert_kwargs_to_snake_case

import domain.shelter_join_requests as join_requests_domain
from api.middlewares import auth_middleware
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def get_my_shelter_join_request_resolver(obj, info, shelter_id):
    logger.api(f"get my join request for {shelter_id}")
    try:
        me = get_request_user(info.context.headers['authorization'])
        join_request = join_requests_domain.get_my_join_request(shelter_id, me.get("id"))
        return {"success": True, "shelter_join_request": join_request}
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_join_requests_resolver(obj, info, shelter_id, status=None):
    logger.api(f"list join requests for {shelter_id} status={status}")
    try:
        me = get_request_user(info.context.headers['authorization'])
        items = join_requests_domain.list_join_requests_for_shelter(
            shelter_id, me.get("id"), status=status
        )
        return {"success": True, "items": items}
    except Exception as e:
        return {**_err(e, info), "items": []}
