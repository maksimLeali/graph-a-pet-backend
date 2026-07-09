from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.notifications as notifications_domain
from api.errors import format_error, error_pagination
from api.middlewares import auth_middleware
from utils import get_request_user, format_common_search
from utils.logger import logger, stringify


@convert_kwargs_to_snake_case
@auth_middleware
def list_my_notifications_resolver(obj, info: GraphQLResolveInfo, search=None):
    logger.api(f"search: {stringify(search)}")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        common_search = format_common_search(search or {})
        items, pagination = notifications_domain.list_my_notifications(
            current_user.get("id"), common_search
        )
        payload = {
            "success": True,
            "items": items,
            "pagination": pagination,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "items": [],
            "pagination": error_pagination,
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_unread_notification_count_resolver(obj, info):
    logger.api("get unread notification count")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        return notifications_domain.get_unread_count(current_user.get("id"))
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
