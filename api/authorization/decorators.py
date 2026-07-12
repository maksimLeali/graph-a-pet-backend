"""GraphQL decorators for permission-first authorization.

Standard usage on a resolver:

    @convert_kwargs_to_snake_case
    @require_permission(ShelterPermissions.TASKS_CREATE, shelter_argument="shelter_id")
    def create_shelter_task_resolver(obj, info, data): ...

Shelter id extraction is declarative (kwarg name, or a field inside an input
dict) so resolvers stop hand-rolling it. Platform permissions omit both.
"""
from functools import wraps
from typing import Any

from graphql import GraphQLError, GraphQLResolveInfo

from api.errors import AuthenticationError, ForbiddenError, format_error
from domain.authorization import authorization_service
from utils import get_request_user
from utils.logger import logger


def _extract_shelter_id(args, shelter_argument=None, input_argument=None, shelter_field=None):
    if shelter_argument:
        value = args.get(shelter_argument)
        if value is not None:
            return value
        data = args.get("data")
        if isinstance(data, dict):
            return data.get(shelter_argument)
        return None
    if input_argument:
        payload = args.get(input_argument)
        if isinstance(payload, dict):
            return payload.get(shelter_field or "shelter_id")
    return None


def require_permission(permission, shelter_argument=None, input_argument=None,
                       shelter_field=None, platform=False):
    """Enforce `permission` before running the resolver.

    - shelter_argument: kwarg holding the shelter id (also looked up inside a
      `data` input dict with the same key);
    - input_argument + shelter_field: input dict kwarg and the field inside it;
    - platform=True: platform-scoped permission, no shelter id expected.

    Raises structured GraphQLError (UNAUTHORIZED / FORBIDDEN /
    INVALID_AUTHORIZATION_SCOPE / MEMBERSHIP_NOT_ACTIVE) on failure.
    """
    def decorate(fn):
        @wraps(fn)
        def wrapper(obj: Any, info: GraphQLResolveInfo, **args):
            token = info.context.headers.get("authorization")
            try:
                try:
                    user = get_request_user(token)
                except Exception:
                    raise AuthenticationError("unauthorized")
                shelter_id = None
                if not platform:
                    shelter_id = _extract_shelter_id(
                        args, shelter_argument, input_argument, shelter_field
                    )
                    if shelter_id is None:
                        raise ForbiddenError("shelter_id required for authorization")
                authorization_service.authorize(
                    user_id=user["id"],
                    permission=permission,
                    shelter_id=shelter_id,
                )
                _touch_user_activity(user["id"])
                return fn(obj, info, **args)
            except Exception as e:
                error = format_error(e, token)
                raise GraphQLError(message=error.get("message"), extensions=error)
        return wrapper
    return decorate


def authorize_from_token(token, permission, shelter_id=None):
    """Imperative variant for resolvers that resolve the shelter id from the
    entity first (update/complete/delete flows). Returns the user dict."""
    try:
        user = get_request_user(token)
    except Exception:
        raise AuthenticationError("unauthorized")
    authorization_service.authorize(
        user_id=user["id"],
        permission=permission,
        shelter_id=shelter_id,
    )
    _touch_user_activity(user["id"])
    return user


def _touch_user_activity(user_id):
    # parity with the legacy auth_middleware, which stamped last_activity
    try:
        from domain.users import update_user_activity
        update_user_activity(user_id)
    except Exception as e:
        logger.warning(f"failed to update user activity: {e}")
