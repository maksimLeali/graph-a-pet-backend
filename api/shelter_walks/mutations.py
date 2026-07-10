from ariadne import convert_kwargs_to_snake_case
import domain.shelter_walks as shelter_walks_domain
from api.middlewares import auth_middleware, assert_shelter_role
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger, stringify


def _ok(walk):
    return {"success": True, "shelter_walk": walk}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_walk_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        shelter_id = shelter_walks_domain.shelter_id_for_shelter_pet(data["shelter_pet_id"])
        assert_shelter_role(token, shelter_id, "STAFF")
        me = get_request_user(token)
        return _ok(shelter_walks_domain.create_shelter_walk(data, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def update_shelter_walk_resolver(obj, info, id, data):
    logger.api(f"id: {id} data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_walks_domain.shelter_id_for_walk(id), "STAFF")
        return _ok(shelter_walks_domain.update_shelter_walk(id, data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def start_shelter_walk_resolver(obj, info, id):
    logger.api(f"id: {id} start")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_walks_domain.shelter_id_for_walk(id), "STAFF")
        return _ok(shelter_walks_domain.start_shelter_walk(id))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def complete_shelter_walk_resolver(obj, info, id, notes=None):
    logger.api(f"id: {id} complete")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_walks_domain.shelter_id_for_walk(id), "STAFF")
        return _ok(shelter_walks_domain.complete_shelter_walk(id, notes))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def set_shelter_walk_manual_duration_resolver(obj, info, id, duration_minutes):
    logger.api(f"id: {id} duration_minutes: {duration_minutes}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_walks_domain.shelter_id_for_walk(id), "STAFF")
        return _ok(shelter_walks_domain.set_manual_duration(id, duration_minutes))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def cancel_shelter_walk_resolver(obj, info, id, reason=None):
    logger.api(f"id: {id} cancel")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_walks_domain.shelter_id_for_walk(id), "STAFF")
        return _ok(shelter_walks_domain.cancel_shelter_walk(id, reason))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def delete_shelter_walk_resolver(obj, info, id):
    logger.api(f"id: {id} remove")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_walks_domain.shelter_id_for_walk(id), "OWNER")
        me = get_request_user(token)
        memoriae_id = shelter_walks_domain.delete_shelter_walk(id, me["id"])
        return {"success": True, "id": memoriae_id}
    except Exception as e:
        return _err(e, info)
