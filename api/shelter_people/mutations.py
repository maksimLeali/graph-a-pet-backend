from ariadne import convert_kwargs_to_snake_case
import domain.shelter_people as people_domain
from api.middlewares import auth_middleware, assert_shelter_role
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger, stringify


def _ok(person=None):
    return {"success": True, "shelter_person": person}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_person_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, data["shelter_id"], "STAFF")
        me = get_request_user(token)
        return _ok(people_domain.create_shelter_person(data, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def update_shelter_person_resolver(obj, info, id, data):
    logger.api(f"id: {id} data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, people_domain.shelter_id_for_person(id), "MANAGER")
        return _ok(people_domain.update_shelter_person(id, data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def archive_shelter_person_resolver(obj, info, id):
    logger.api(f"id: {id} archive")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, people_domain.shelter_id_for_person(id), "MANAGER")
        me = get_request_user(token)
        return _ok(people_domain.archive_shelter_person(id, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def link_shelter_person_to_user_resolver(obj, info, person_id, user_id):
    logger.api(f"link person {person_id} to user {user_id}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, people_domain.shelter_id_for_person(person_id), "OWNER")
        return _ok(people_domain.link_shelter_person_to_user(person_id, user_id))
    except Exception as e:
        return _err(e, info)
