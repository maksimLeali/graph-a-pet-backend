"""Central shelter permission model.

Single source of truth for:
  * the shelter role hierarchy (VOLUNTEER < STAFF < MANAGER < OWNER)
  * the capability -> minimum-role matrix (mirrors the spec's role table)
  * the assertion helpers used by resolvers

Resolvers must not hard-code role strings ad hoc; call `assert_capability`
(or the `require_capability` decorator) so the policy lives in one place.
"""
from functools import wraps
from typing import Any

from graphql import GraphQLResolveInfo, GraphQLError
from api.errors import format_error, ForbiddenError
from repository.users.models import UserRole
from utils import get_request_user
from utils.logger import logger

# --- role hierarchy (higher number = more power) ---
ROLE_LEVEL = {"VOLUNTEER": 1, "STAFF": 2, "MANAGER": 3, "OWNER": 4}


# --- capability -> minimum shelter role ---
# VOLUNTEER: read only
# STAFF: complete/skip tasks, walks, box check-in/out, inventory movements
# MANAGER: manage tasks, boxes, inventory items
# OWNER: shelter info, roles
# (system-level delete stays a global ADMIN check, handled separately)
class Cap:
    READ = "shelter.read"

    TASK_COMPLETE = "task.complete"
    TASK_SKIP = "task.skip"
    WALK_RECORD = "walk.record"
    BOX_CHECK_IN_OUT = "box.checkin"
    INVENTORY_MOVEMENT = "inventory.movement"

    TASK_MANAGE = "task.manage"
    BOX_MANAGE = "box.manage"
    INVENTORY_ITEM_MANAGE = "inventory.item.manage"

    SHELTER_EDIT = "shelter.edit"
    ROLE_MANAGE = "role.manage"

    INVENTORY_NEGATIVE_OVERRIDE = "inventory.negative_override"


CAPABILITY_MIN_ROLE = {
    Cap.READ: "VOLUNTEER",

    Cap.TASK_COMPLETE: "STAFF",
    Cap.TASK_SKIP: "STAFF",
    Cap.WALK_RECORD: "STAFF",
    Cap.BOX_CHECK_IN_OUT: "STAFF",
    Cap.INVENTORY_MOVEMENT: "STAFF",

    Cap.TASK_MANAGE: "MANAGER",
    Cap.BOX_MANAGE: "MANAGER",
    Cap.INVENTORY_ITEM_MANAGE: "MANAGER",
    Cap.INVENTORY_NEGATIVE_OVERRIDE: "MANAGER",

    Cap.SHELTER_EDIT: "OWNER",
    Cap.ROLE_MANAGE: "OWNER",
}


def user_shelter_level(user_id, shelter_id):
    """Highest role level (int) the user holds on the shelter; 0 if none."""
    # late import avoids middlewares/domain/api import cycle
    import domain.shelter_roles as shelter_roles_domain
    roles = shelter_roles_domain.get_user_roles_on_shelter(user_id, shelter_id) or []
    levels = [ROLE_LEVEL.get((r.get("role") or "").upper(), 0) for r in roles]
    return max(levels) if levels else 0


def is_restricted_to_assigned(user, shelter_id):
    """True when the user only sees what is assigned to them on this shelter:
    highest role below STAFF (i.e. VOLUNTEER). Global ADMIN is never
    restricted."""
    if user.get("role") == UserRole.ADMIN.name:
        return False
    return user_shelter_level(user["id"], shelter_id) < ROLE_LEVEL["STAFF"]


def has_capability(user, shelter_id, capability):
    """True if `user` (dict) can perform `capability` on `shelter_id`.
    Global ADMIN always passes."""
    required_role = CAPABILITY_MIN_ROLE[capability]
    if user.get("role") == UserRole.ADMIN.name:
        allowed = True
    else:
        allowed = user_shelter_level(user["id"], shelter_id) >= ROLE_LEVEL[required_role]
    # shadow-compare with RBAC (log-only); late import avoids cycles
    from domain.authorization.shadow import compare_shelter_decision
    compare_shelter_decision(user["id"], shelter_id, required_role, legacy_allowed=allowed)
    return allowed


def assert_capability(token, shelter_id, capability):
    """Raise ForbiddenError unless the token's user has `capability` on the
    shelter. Returns the user dict on success."""
    user = get_request_user(token)
    if not has_capability(user, shelter_id, capability):
        logger.error(
            f"{user.get('id')} lacks capability {capability} on shelter {shelter_id}"
        )
        raise ForbiddenError(f"missing capability: {capability}")
    return user


def require_capability(capability):
    """Decorator: enforce `capability` on the resolver's shelter.
    Resolves the shelter id from `shelter_id` kwarg or `data['shelter_id']`."""
    def decorate(fn):
        @wraps(fn)
        def wrapper(obj: Any, info: GraphQLResolveInfo, **args):
            try:
                token = info.context.headers['authorization']
                shelter_id = args.get("shelter_id")
                if shelter_id is None and isinstance(args.get("data"), dict):
                    shelter_id = args["data"].get("shelter_id")
                if shelter_id is None:
                    raise ForbiddenError("shelter_id required for authorization")
                assert_capability(token, shelter_id, capability)
                return fn(obj, info, **args)
            except Exception as e:
                error = format_error(e, info.context.headers['authorization'])
                raise GraphQLError(message=error.get('message'), extensions=error)
        return wrapper
    return decorate
