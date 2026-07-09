from ariadne import convert_kwargs_to_snake_case
import domain.shelter_claim_requests as claims_domain
from api.middlewares import auth_middleware, min_role
from api.errors import format_error
from repository.users.models import UserRole
from utils import get_request_user
from utils.logger import logger, stringify


def _ok(claim=None):
    return {"success": True, "shelter_claim_request": claim}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def request_shelter_claim_resolver(obj, info, shelter_id, data=None):
    logger.api(f"shelter_id: {shelter_id} data: {stringify(data)}")
    try:
        me = get_request_user(info.context.headers['authorization'])
        claim = claims_domain.request_claim(shelter_id, data, me["id"])
        return _ok(claim)
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def cancel_shelter_claim_resolver(obj, info, id):
    logger.api(f"id: {id} cancel")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(claims_domain.cancel_claim(id, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def approve_shelter_claim_resolver(obj, info, id, decision_note=None):
    logger.api(f"id: {id} approve")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(claims_domain.approve_claim(id, decision_note, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@min_role(UserRole.ADMIN.name)
def reject_shelter_claim_resolver(obj, info, id, decision_note=None):
    logger.api(f"id: {id} reject")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(claims_domain.reject_claim(id, decision_note, me["id"]))
    except Exception as e:
        return _err(e, info)
