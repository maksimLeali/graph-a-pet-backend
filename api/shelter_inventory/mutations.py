from ariadne import convert_kwargs_to_snake_case
import domain.shelter_inventory as inventory_domain
from api.middlewares import auth_middleware, assert_shelter_role
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
        assert_shelter_role(token, data["shelter_id"], "MANAGER")
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
        assert_shelter_role(token, inventory_domain.shelter_id_for_item(id), "MANAGER")
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
        assert_shelter_role(token, inventory_domain.shelter_id_for_item(id), "OWNER")
        me = get_request_user(token)
        memoriae_id = inventory_domain.delete_shelter_inventory_item(id, me["id"])
        return {"success": True, "id": memoriae_id}
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_inventory_movement_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, inventory_domain.shelter_id_for_item(data["item_id"]), "STAFF")
        me = get_request_user(token)
        movement = inventory_domain.create_shelter_inventory_movement(data, me["id"])
        return {"success": True, "movement": movement}
    except Exception as e:
        return _err(e, info)
