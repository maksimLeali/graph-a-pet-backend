from ariadne import convert_kwargs_to_snake_case
import domain.shelter_boxes as shelter_boxes_domain
import domain.shelter_maps as shelter_maps_domain
from api.middlewares import auth_middleware, assert_shelter_role
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger, stringify


def _ok(box):
    return {"success": True, "box": box}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_box_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        shelter_map = shelter_maps_domain.get_shelter_map(data["map_id"])
        assert_shelter_role(token, shelter_map["shelter_id"], "MANAGER")
        return _ok(shelter_boxes_domain.create_shelter_box(data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def update_shelter_box_resolver(obj, info, id, data):
    logger.api(f"id: {id}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_boxes_domain.shelter_id_for_box(id), "MANAGER")
        return _ok(shelter_boxes_domain.update_shelter_box(id, data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def mark_box_cleaned_resolver(obj, info, box_id):
    logger.api(f"box_id: {box_id} cleaned")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_boxes_domain.shelter_id_for_box(box_id), "STAFF")
        return _ok(shelter_boxes_domain.mark_box_cleaned(box_id))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def set_box_out_of_service_resolver(obj, info, box_id, out_of_service):
    logger.api(f"box_id: {box_id} oos: {out_of_service}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_boxes_domain.shelter_id_for_box(box_id), "STAFF")
        return _ok(shelter_boxes_domain.set_box_out_of_service(box_id, out_of_service))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def delete_shelter_box_resolver(obj, info, id):
    logger.api(f"id: {id} remove")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_boxes_domain.shelter_id_for_box(id), "OWNER")
        me = get_request_user(token)
        memoriae_id = shelter_boxes_domain.delete_shelter_box(id, me["id"])
        return {"success": True, "id": memoriae_id}
    except Exception as e:
        return _err(e, info)
