from ariadne import convert_kwargs_to_snake_case
import domain.shelter_walks as shelter_walks_domain
from api.middlewares import auth_middleware, assert_shelter_role
from api.permissions import assert_capability, Cap, is_restricted_to_assigned
from api.errors import format_error, ForbiddenError
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


def assert_staff_or_own_walk(token, walk_id):
    """STAFF+ may act on any walk of the shelter; below STAFF (volunteers)
    only on walks where they are the walker, directly or through their
    linked shelter_person. Returns the user dict."""
    walk = shelter_walks_domain.get_shelter_walk(walk_id)
    shelter_id = shelter_walks_domain.shelter_id_for_shelter_pet(walk["shelter_pet_id"])
    user = assert_capability(token, shelter_id, Cap.READ)
    if not is_restricted_to_assigned(user, shelter_id):
        return user
    if walk.get("walker_id") == user["id"]:
        return user
    if walk.get("shelter_person_id"):
        import repository.shelter_people as shelter_people_data
        if walk["shelter_person_id"] in shelter_people_data.get_person_ids_for_user(
            user["id"], shelter_id
        ):
            return user
    raise ForbiddenError("volunteers can only act on their own walks")


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_walk_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        shelter_id = shelter_walks_domain.shelter_id_for_shelter_pet(data["shelter_pet_id"])
        me = assert_capability(token, shelter_id, Cap.READ)
        if is_restricted_to_assigned(me, shelter_id):
            # volunteers plan only for pets assigned to them, as their own walker
            import repository.shelter_pets as shelter_pets_data
            assigned = shelter_pets_data.get_assigned_shelter_pet_ids(me["id"], shelter_id)
            if data["shelter_pet_id"] not in assigned:
                raise ForbiddenError(
                    "volunteers can only plan walks for pets assigned to them"
                )
            data = {**data, "walker_id": me["id"], "shelter_person_id": None}
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
        assert_staff_or_own_walk(token, id)
        return _ok(shelter_walks_domain.start_shelter_walk(id))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def complete_shelter_walk_resolver(obj, info, id, notes=None):
    logger.api(f"id: {id} complete")
    try:
        token = info.context.headers['authorization']
        assert_staff_or_own_walk(token, id)
        return _ok(shelter_walks_domain.complete_shelter_walk(id, notes))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def set_shelter_walk_manual_duration_resolver(obj, info, id, duration_minutes):
    logger.api(f"id: {id} duration_minutes: {duration_minutes}")
    try:
        token = info.context.headers['authorization']
        assert_staff_or_own_walk(token, id)
        return _ok(shelter_walks_domain.set_manual_duration(id, duration_minutes))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def cancel_shelter_walk_resolver(obj, info, id, reason=None):
    logger.api(f"id: {id} cancel")
    try:
        token = info.context.headers['authorization']
        assert_staff_or_own_walk(token, id)
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
