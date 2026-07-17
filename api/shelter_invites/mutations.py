from ariadne import convert_kwargs_to_snake_case
import domain.shelter_invites as shelter_invites_domain
from api.middlewares import auth_middleware
from api.authorization.decorators import require_permission
from domain.authorization.catalog import ShelterPermissions
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger, stringify


def _ok(invite=None):
    return {"success": True, "shelter_invite": invite}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.MEMBERS_INVITE, shelter_argument="shelter_id")
def create_shelter_invite_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(shelter_invites_domain.create_shelter_invite(data, me.get("id")))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def accept_shelter_invite_resolver(obj, info, id):
    logger.api(f"accept shelter invite {id}")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(shelter_invites_domain.accept_shelter_invite(id, me.get("id")))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def reject_shelter_invite_resolver(obj, info, id):
    logger.api(f"reject shelter invite {id}")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(shelter_invites_domain.reject_shelter_invite(id, me.get("id")))
    except Exception as e:
        return _err(e, info)
