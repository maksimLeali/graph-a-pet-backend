from ariadne import convert_kwargs_to_snake_case
import domain.shelter_ownership_transfers as transfers_domain
from api.middlewares import auth_middleware
from api.authorization.decorators import authorize_from_token
from domain.authorization.catalog import ShelterPermissions
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger, stringify


def _ok(transfer=None):
    return {"success": True, "shelter_ownership_transfer": transfer}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def request_shelter_ownership_transfer_resolver(obj, info, shelter_id, to_user_id, new_role_for_previous_owner=None):
    logger.api(f"shelter_id: {shelter_id} to_user_id: {to_user_id}")
    try:
        token = info.context.headers['authorization']
        authorize_from_token(token, ShelterPermissions.OWNERSHIP_TRANSFER, shelter_id=shelter_id)
        me = get_request_user(token)
        transfer = transfers_domain.request_transfer(
            shelter_id, to_user_id, new_role_for_previous_owner, me["id"]
        )
        return _ok(transfer)
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def accept_shelter_ownership_transfer_resolver(obj, info, id):
    logger.api(f"id: {id} accept")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(transfers_domain.accept_transfer(id, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def reject_shelter_ownership_transfer_resolver(obj, info, id):
    logger.api(f"id: {id} reject")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(transfers_domain.reject_transfer(id, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def cancel_shelter_ownership_transfer_resolver(obj, info, id):
    logger.api(f"id: {id} cancel")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(transfers_domain.cancel_transfer(id, me["id"]))
    except Exception as e:
        return _err(e, info)
