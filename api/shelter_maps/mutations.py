from ariadne import convert_kwargs_to_snake_case
import domain.shelter_maps as shelter_maps_domain
from api.middlewares import auth_middleware, min_shelter_role, assert_shelter_role
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger, stringify


def _ok(m):
    return {"success": True, "map": m}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@min_shelter_role("MANAGER")
def create_shelter_map_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        return _ok(shelter_maps_domain.create_shelter_map(data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def update_shelter_map_resolver(obj, info, id, data):
    logger.api(f"id: {id}")
    try:
        token = info.context.headers['authorization']
        shelter_map = shelter_maps_domain.get_shelter_map(id)
        assert_shelter_role(token, shelter_map["shelter_id"], "MANAGER")
        return _ok(shelter_maps_domain.update_shelter_map(id, data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def save_shelter_map_layout_resolver(obj, info, map_id, data):
    logger.api(f"map_id: {map_id} layout")
    try:
        token = info.context.headers['authorization']
        shelter_map = shelter_maps_domain.get_shelter_map(map_id)
        assert_shelter_role(token, shelter_map["shelter_id"], "MANAGER")
        return _ok(shelter_maps_domain.save_layout(map_id, data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def delete_shelter_map_resolver(obj, info, id):
    logger.api(f"id: {id} remove")
    try:
        token = info.context.headers['authorization']
        shelter_map = shelter_maps_domain.get_shelter_map(id)
        assert_shelter_role(token, shelter_map["shelter_id"], "OWNER")
        me = get_request_user(token)
        memoriae_id = shelter_maps_domain.delete_shelter_map(id, me["id"])
        return {"success": True, "id": memoriae_id}
    except Exception as e:
        return _err(e, info)
