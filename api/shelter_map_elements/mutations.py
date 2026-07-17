from ariadne import convert_kwargs_to_snake_case
import domain.shelter_map_elements as elements_domain
import domain.shelter_maps as shelter_maps_domain
from api.middlewares import auth_middleware
from api.authorization.decorators import authorize_from_token
from domain.authorization.catalog import ShelterPermissions
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger, stringify


def _ok(element):
    return {"success": True, "element": element}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_map_element_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        shelter_map = shelter_maps_domain.get_shelter_map(data["map_id"])
        authorize_from_token(token, ShelterPermissions.MAP_UPDATE, shelter_id=shelter_map["shelter_id"])
        return _ok(elements_domain.create_shelter_map_element(data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def update_shelter_map_element_resolver(obj, info, id, data):
    logger.api(f"id: {id}")
    try:
        token = info.context.headers['authorization']
        authorize_from_token(token, ShelterPermissions.MAP_UPDATE, shelter_id=elements_domain.shelter_id_for_element(id))
        return _ok(elements_domain.update_shelter_map_element(id, data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def delete_shelter_map_element_resolver(obj, info, id):
    logger.api(f"id: {id} remove")
    try:
        token = info.context.headers['authorization']
        authorize_from_token(token, ShelterPermissions.MAP_UPDATE, shelter_id=elements_domain.shelter_id_for_element(id))
        me = get_request_user(token)
        memoriae_id = elements_domain.delete_shelter_map_element(id, me["id"])
        return {"success": True, "id": memoriae_id}
    except Exception as e:
        return _err(e, info)
