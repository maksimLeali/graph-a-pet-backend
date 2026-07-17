from ariadne import convert_kwargs_to_snake_case
import domain.shelter_maps as shelter_maps_domain
from api.middlewares import auth_middleware
from api.authorization.decorators import authorize_from_token, require_permission
from domain.authorization.catalog import ShelterPermissions
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
@require_permission(ShelterPermissions.MAP_UPDATE, shelter_argument="shelter_id")
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
        authorize_from_token(token, ShelterPermissions.MAP_UPDATE, shelter_id=shelter_map["shelter_id"])
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
        authorize_from_token(token, ShelterPermissions.MAP_UPDATE, shelter_id=shelter_map["shelter_id"])
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
        authorize_from_token(token, ShelterPermissions.MAP_UPDATE, shelter_id=shelter_map["shelter_id"])
        me = get_request_user(token)
        memoriae_id = shelter_maps_domain.delete_shelter_map(id, me["id"])
        return {"success": True, "id": memoriae_id}
    except Exception as e:
        return _err(e, info)
