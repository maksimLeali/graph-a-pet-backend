from ariadne import convert_kwargs_to_snake_case

from api.errors import AuthenticationError, format_error
from api.authorization.decorators import require_permission
from domain.authorization import authorization_service
from domain.authorization.catalog import PlatformPermissions
from utils import get_request_user
from utils.logger import logger


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.BACKOFFICE_ACCESS, platform=True)
def list_permission_catalog_resolver(obj, info):
    from domain.authorization.catalog import PERMISSION_CATALOG
    return [
        {
            "key": p["key"],
            "domain": p["domain"],
            "scope_type": p["scope_type"],
            "risk_level": p["risk_level"],
        }
        for p in PERMISSION_CATALOG
    ]


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.BACKOFFICE_ACCESS, platform=True)
def list_rbac_roles_resolver(obj, info):
    import repository.authorization as authz_data
    try:
        roles = authz_data.list_roles_with_permissions()
        return {"success": True, "roles": roles}
    except Exception as e:
        logger.error(e)
        return {"success": False, "error": format_error(e, None), "roles": []}


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.USERS_READ, platform=True)
def get_user_rbac_roles_resolver(obj, info, user_id):
    import repository.authorization as authz_data
    try:
        assignments = authz_data.list_user_role_assignments(user_id)
        platform_perms = sorted(
            p for p in authorization_service.effective_permissions(user_id)
            if p.startswith("platform.")
        )
        result = []
        for a in assignments:
            result.append({
                "id": a["id"],
                "role_id": a["role_id"],
                "role_code": a["role"]["code"],
                "role_name": a["role"]["name"],
                "scope_type": a["role"]["scope_type"],
                "shelter_id": a.get("shelter_id"),
                "status": a["status"],
                "valid_from": a.get("valid_from"),
                "valid_until": a.get("valid_until"),
                "assigned_at": a["created_at"],
            })
        return {
            "success": True,
            "assignments": result,
            "effective_platform_permissions": platform_perms,
        }
    except Exception as e:
        logger.error(e)
        return {
            "success": False,
            "error": format_error(e, None),
            "assignments": [],
            "effective_platform_permissions": [],
        }


@convert_kwargs_to_snake_case
def my_shelter_authorization_resolver(obj, info, shelter_id):
    """Effective permissions + membership status of the caller on one shelter.
    The frontend consumes this instead of deriving capabilities from role names."""
    logger.api(f"shelter_id: {shelter_id}")
    token = info.context.headers.get("authorization")
    try:
        try:
            user = get_request_user(token)
        except Exception:
            raise AuthenticationError("unauthorized")
        permissions = authorization_service.effective_permissions(
            user["id"], shelter_id=shelter_id
        )
        return {
            "success": True,
            "authorization": {
                "shelter_id": shelter_id,
                "membership_status": authorization_service.membership_status(
                    user["id"], shelter_id
                ),
                "permissions": sorted(permissions),
            },
        }
    except Exception as e:
        logger.error(e)
        return {"success": False, "error": format_error(e, token)}
