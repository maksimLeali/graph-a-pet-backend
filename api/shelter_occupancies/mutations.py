from ariadne import convert_kwargs_to_snake_case
import domain.shelter_occupancies as occupancies_domain
from api.middlewares import auth_middleware, assert_shelter_role
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger, stringify


def _ok(occ):
    return {"success": True, "occupancy": occ}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def assign_pet_to_box_resolver(obj, info, box_id, shelter_pet_id, reason=None):
    logger.api(f"assign pet {shelter_pet_id} -> box {box_id}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, occupancies_domain.shelter_id_for_box(box_id), "STAFF")
        me = get_request_user(token)
        return _ok(occupancies_domain.assign_pet_to_box(box_id, shelter_pet_id, me["id"], reason))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def release_pet_from_box_resolver(obj, info, occupancy_id, reason=None):
    logger.api(f"release occupancy {occupancy_id}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, occupancies_domain.shelter_id_for_occupancy(occupancy_id), "STAFF")
        me = get_request_user(token)
        return _ok(occupancies_domain.release_pet_from_box(occupancy_id, me["id"], reason))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def move_pet_between_boxes_resolver(obj, info, shelter_pet_id, to_box_id, reason=None):
    logger.api(f"move pet {shelter_pet_id} -> box {to_box_id}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, occupancies_domain.shelter_id_for_box(to_box_id), "STAFF")
        me = get_request_user(token)
        return _ok(occupancies_domain.move_pet_between_boxes(shelter_pet_id, to_box_id, me["id"], reason))
    except Exception as e:
        return _err(e, info)
