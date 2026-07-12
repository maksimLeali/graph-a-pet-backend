from ariadne import convert_kwargs_to_snake_case
import domain.shelter_tasks as shelter_tasks_domain
from api.authorization.decorators import require_permission, authorize_from_token
from api.errors import format_error
from domain.authorization.catalog import ShelterPermissions
from utils.logger import logger, stringify


def _ok(task):
    return {"success": True, "shelter_task": task}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.TASKS_CREATE, shelter_argument="shelter_id")
def create_shelter_task_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        return _ok(shelter_tasks_domain.create_shelter_task(data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
def update_shelter_task_resolver(obj, info, id, data):
    logger.api(f"id: {id} data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        task = shelter_tasks_domain.get_shelter_task(id)
        authorize_from_token(token, ShelterPermissions.TASKS_UPDATE, task["shelter_id"])
        return _ok(shelter_tasks_domain.update_shelter_task(id, data))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
def complete_shelter_task_resolver(obj, info, id, notes=None):
    logger.api(f"id: {id} complete")
    try:
        token = info.context.headers['authorization']
        task = shelter_tasks_domain.get_shelter_task(id)
        me = authorize_from_token(token, ShelterPermissions.TASKS_EXECUTE, task["shelter_id"])
        return _ok(shelter_tasks_domain.complete_shelter_task(id, me["id"], notes))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
def skip_shelter_task_resolver(obj, info, id, reason=None):
    logger.api(f"id: {id} skip")
    try:
        token = info.context.headers['authorization']
        task = shelter_tasks_domain.get_shelter_task(id)
        me = authorize_from_token(token, ShelterPermissions.TASKS_EXECUTE, task["shelter_id"])
        return _ok(shelter_tasks_domain.skip_shelter_task(id, me["id"], reason))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
def delete_shelter_task_resolver(obj, info, id):
    logger.api(f"id: {id} remove")
    try:
        token = info.context.headers['authorization']
        task = shelter_tasks_domain.get_shelter_task(id)
        me = authorize_from_token(token, ShelterPermissions.TASKS_DELETE, task["shelter_id"])
        memoriae_id = shelter_tasks_domain.delete_shelter_task(id, me["id"])
        return {"success": True, "id": memoriae_id}
    except Exception as e:
        return _err(e, info)
