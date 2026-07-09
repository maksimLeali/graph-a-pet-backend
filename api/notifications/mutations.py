from ariadne import convert_kwargs_to_snake_case
import domain.notifications as notifications_domain
from api.errors import format_error
from api.middlewares import auth_middleware
from utils import get_request_user
from utils.logger import logger


def _ok(notification=None):
    return {"success": True, "notification": notification}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def mark_notification_as_read_resolver(obj, info, id):
    logger.api(f"id: {id} mark read")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(notifications_domain.mark_as_read(id, me.get("id")))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def mark_all_notifications_as_read_resolver(obj, info):
    logger.api("mark all notifications read")
    try:
        me = get_request_user(info.context.headers['authorization'])
        notifications_domain.mark_all_as_read(me.get("id"))
        return _ok()
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def dismiss_notification_resolver(obj, info, id):
    logger.api(f"id: {id} dismiss")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(notifications_domain.dismiss(id, me.get("id")))
    except Exception as e:
        return _err(e, info)
