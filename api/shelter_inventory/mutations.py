from ariadne import convert_kwargs_to_snake_case
import domain.shelter_inventory as inventory_domain
from api.middlewares import auth_middleware
from api.authorization.decorators import authorize_from_token
from domain.authorization.catalog import ShelterPermissions
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger, stringify


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_inventory_item_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        authorize_from_token(token, ShelterPermissions.INVENTORY_MANAGE, shelter_id=data["shelter_id"])
        me = get_request_user(token)
        item = inventory_domain.create_shelter_inventory_item(data, me["id"])
        return {"success": True, "item": item}
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def update_shelter_inventory_item_resolver(obj, info, id, data):
    logger.api(f"id: {id}")
    try:
        token = info.context.headers['authorization']
        authorize_from_token(token, ShelterPermissions.INVENTORY_MANAGE, shelter_id=inventory_domain.shelter_id_for_item(id))
        item = inventory_domain.update_shelter_inventory_item(id, data)
        return {"success": True, "item": item}
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def delete_shelter_inventory_item_resolver(obj, info, id):
    logger.api(f"id: {id} remove")
    try:
        token = info.context.headers['authorization']
        authorize_from_token(token, ShelterPermissions.INVENTORY_MANAGE, shelter_id=inventory_domain.shelter_id_for_item(id))
        me = get_request_user(token)
        memoriae_id = inventory_domain.delete_shelter_inventory_item(id, me["id"])
        return {"success": True, "id": memoriae_id}
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def archive_shelter_inventory_item_resolver(obj, info, id):
    logger.api(f"id: {id} archive")
    try:
        token = info.context.headers['authorization']
        authorize_from_token(token, ShelterPermissions.INVENTORY_MANAGE, shelter_id=inventory_domain.shelter_id_for_item(id))
        me = get_request_user(token)
        item = inventory_domain.archive_shelter_inventory_item(id, me["id"])
        return {"success": True, "item": item}
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_inventory_movement_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        shelter_id = inventory_domain.shelter_id_for_item(data["item_id"])
        authorize_from_token(token, ShelterPermissions.INVENTORY_CONSUME, shelter_id=shelter_id)
        # negative-stock override is a privileged action (MANAGER+)
        allow_negative = bool(data.pop("allow_negative", False))
        if allow_negative:
            authorize_from_token(token, ShelterPermissions.INVENTORY_ADJUST, shelter_id=shelter_id)
        me = get_request_user(token)
        movement = inventory_domain.create_shelter_inventory_movement(
            data, me["id"], allow_negative=allow_negative
        )
        return {"success": True, "movement": movement}
    except Exception as e:
        return _err(e, info)
