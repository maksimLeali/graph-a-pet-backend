from ariadne import convert_kwargs_to_snake_case

from api.authorization.decorators import require_permission
from api.errors import format_error
from domain.authorization.catalog import PlatformPermissions
from utils.logger import logger
from repository import db


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
