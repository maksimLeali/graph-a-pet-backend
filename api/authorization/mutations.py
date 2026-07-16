from ariadne import convert_kwargs_to_snake_case

from api.authorization.decorators import require_permission
from api.errors import format_error
from domain.authorization.catalog import PlatformPermissions
from utils import get_request_user
from utils.logger import logger
from repository import db


def _assignment_payload(assignment, role):
    """Shape an assignment dict + its role dict as UserRbacAssignment."""
    return {
        "id": assignment["id"],
        "role_id": assignment["role_id"],
        "role_code": role["code"],
        "role_name": role["name"],
        "scope_type": role["scope_type"],
        "shelter_id": assignment.get("shelter_id"),
        "status": assignment["status"],
        "valid_from": assignment.get("valid_from"),
        "valid_until": assignment.get("valid_until"),
        "assigned_at": assignment["created_at"],
    }


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.ROLES_MANAGE, platform=True)
def create_rbac_role_resolver(obj, info, input):
    import repository.authorization as authz_data
    try:
        role = authz_data.create_custom_role(
            code=input["code"],
            name=input["name"],
            description=input.get("description"),
            scope_type=input["scope_type"],
        )
        perm_keys = input.get("permission_keys") or []
        if perm_keys:
            authz_data.sync_role_permissions(role["id"], perm_keys)
        role["permissions"] = sorted(perm_keys)
        db.session.commit()
        return {"success": True, "role": role}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return {"success": False, "error": format_error(e, None), "role": None}


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.ROLES_MANAGE, platform=True)
def update_rbac_role_permissions_resolver(obj, info, input):
    import repository.authorization as authz_data
    try:
        role_id = input["role_id"]
        perm_keys = input.get("permission_keys") or []
        authz_data.sync_role_permissions(role_id, perm_keys)
        roles = authz_data.list_roles_with_permissions()
        role = next((r for r in roles if r["id"] == role_id), None)
        if not role:
            raise ValueError("role not found")
        db.session.commit()
        return {"success": True, "role": role}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return {"success": False, "error": format_error(e, None), "role": None}


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.ROLES_MANAGE, platform=True)
def archive_rbac_role_resolver(obj, info, role_id):
    import repository.authorization as authz_data
    try:
        role = authz_data.archive_role(role_id)
        role["permissions"] = []
        db.session.commit()
        return {"success": True, "role": role}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return {"success": False, "error": format_error(e, None), "role": None}


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.ROLES_MANAGE, platform=True)
def assign_rbac_role_to_user_resolver(obj, info, user_id, role_id, shelter_id=None):
    import repository.authorization as authz_data
    try:
        role = authz_data.get_role(role_id)
        if role is None:
            raise ValueError(f"no role found with id {role_id}")
        if role["scope_type"] == "SHELTER" and not shelter_id:
            raise ValueError("shelter_id is required for shelter-scoped roles")
        if role["scope_type"] == "PLATFORM" and shelter_id:
            raise ValueError("shelter_id must be empty for platform-scoped roles")
        me = get_request_user(info.context.headers['authorization'])
        assignment, _created = authz_data.admin_assign_user_role(
            user_id, role_id, shelter_id=shelter_id, assigned_by_id=me.get("id"),
        )
        db.session.commit()
        return {"success": True, "assignment": _assignment_payload(assignment, role)}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return {"success": False, "error": format_error(e, None), "assignment": None}


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.ROLES_MANAGE, platform=True)
def revoke_rbac_role_assignment_resolver(obj, info, assignment_id):
    import repository.authorization as authz_data
    try:
        me = get_request_user(info.context.headers['authorization'])
        assignment = authz_data.revoke_user_role_assignment(assignment_id, me.get("id"))
        role = authz_data.get_role(assignment["role_id"])
        db.session.commit()
        return {"success": True, "assignment": _assignment_payload(assignment, role)}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        return {"success": False, "error": format_error(e, None), "assignment": None}
