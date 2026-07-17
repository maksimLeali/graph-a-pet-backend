from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError

from api.errors import AuthenticationError, format_error
from api.authorization.decorators import require_permission
from domain.authorization import authorization_service
from domain.authorization.catalog import PlatformPermissions, ShelterPermissions
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
def backoffice_access_context_resolver(obj, info):
    """Bootstrap del back office: permission platform effettive + tutti e soli
    i rifugi accessibili (membership ACTIVE, assignment attivo,
    shelters.backoffice.access). I role code sono informativi: le decisioni
    autorizzative usano SOLO le permission."""
    token = info.context.headers.get("authorization")
    try:
        try:
            user = get_request_user(token)
        except Exception:
            raise AuthenticationError("unauthorized")

        platform_permissions = sorted(
            p
            for p in authorization_service.effective_permissions(user["id"])
            if p.startswith("platform.")
        )

        import repository.authorization as authz_data

        shelters = []
        for entry in authz_data.list_user_shelter_access(user["id"]):
            shelter = entry["shelter"]
            membership = entry.get("membership")
            # membership assente = riga legacy pre-RBAC: tollerata come nel
            # AuthorizationService (loggata lì), esposta come ACTIVE
            membership_status = membership["status"] if membership else "ACTIVE"
            if membership_status != "ACTIVE":
                continue
            breakdown = authorization_service.shelter_access_breakdown(
                user["id"], shelter["id"]
            )
            # in questa lista l'accesso è SEMPRE via membership: il gate deve
            # venire dal canale membership, non da un privilegio platform
            if (
                ShelterPermissions.BACKOFFICE_ACCESS
                not in breakdown["membership_permissions"]
            ):
                continue
            permissions = sorted(breakdown["effective"])
            import domain.shelter_ownerships as ownership_service
            shelters.append(
                {
                    "shelter": shelter,
                    "membership_status": membership_status,
                    "roles": entry["role_codes"],
                    "permissions": permissions,
                    "is_technical_owner": ownership_service.is_active_owner(
                        user["id"], shelter["id"]
                    ),
                    "access_mode": "MEMBERSHIP",
                    # true se i privilegi platform aggiungono permission oltre
                    # quelle della membership (da mostrare, mai da usare per
                    # autorizzare lato client)
                    "platform_override_active": bool(
                        breakdown["effective"]
                        - breakdown["membership_permissions"]
                    ),
                }
            )

        return {
            "platform_permissions": platform_permissions,
            "shelters": shelters,
        }
    except Exception as e:
        logger.error(e)
        error = format_error(e, token)
        raise GraphQLError(message=error.get("message"), extensions=error)


@convert_kwargs_to_snake_case
def backoffice_shelter_access_resolver(obj, info, shelter_id):
    """Accesso del chiamante a UN rifugio, con canale esplicito:

    - MEMBERSHIP: assignment shelter-scoped attivi + membership ACTIVE con
      shelters.backoffice.access;
    - PLATFORM_ADMIN: nessuna membership utilizzabile, accesso concesso dal
      solo privilegio platform (grants_all). Nessuna membership o ruolo viene
      creato implicitamente; le operazioni sensibili in questa modalità sono
      tracciate in audit dall'AuthorizationService.
    """
    token = info.context.headers.get("authorization")
    try:
        try:
            user = get_request_user(token)
        except Exception:
            raise AuthenticationError("unauthorized")

        from api.errors import ForbiddenError
        import domain.shelters as shelters_domain

        breakdown = authorization_service.shelter_access_breakdown(
            user["id"], shelter_id
        )
        membership = breakdown["membership"]
        membership_status = membership["status"] if membership else None

        if (
            ShelterPermissions.BACKOFFICE_ACCESS
            in breakdown["membership_permissions"]
        ):
            access_mode = "MEMBERSHIP"
            # tolleranza legacy: assignment senza riga membership
            if membership_status is None:
                membership_status = "ACTIVE"
        elif ShelterPermissions.BACKOFFICE_ACCESS in breakdown["effective"]:
            # concesso solo dal canale platform (es. PLATFORM_ADMIN grants_all)
            access_mode = "PLATFORM_ADMIN"
        else:
            raise ForbiddenError(
                "missing permission: shelters.backoffice.access"
            )

        shelter = shelters_domain.get_shelter(shelter_id)
        import domain.shelter_ownerships as ownership_service
        return {
            "shelter": shelter,
            "membership_status": membership_status,
            "roles": breakdown["shelter_role_codes"],
            "permissions": sorted(breakdown["effective"]),
            "is_technical_owner": ownership_service.is_active_owner(
                user["id"], shelter_id
            ),
            "access_mode": access_mode,
            "platform_override_active": bool(
                breakdown["effective"] - breakdown["membership_permissions"]
            ),
        }
    except Exception as e:
        logger.error(e)
        error = format_error(e, token)
        raise GraphQLError(message=error.get("message"), extensions=error)


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
        breakdown = authorization_service.shelter_access_breakdown(
            user["id"], shelter_id
        )
        import domain.shelter_ownerships as ownership_service
        return {
            "success": True,
            "authorization": {
                "shelter_id": shelter_id,
                "membership_status": authorization_service.membership_status(
                    user["id"], shelter_id
                ),
                "permissions": sorted(breakdown["effective"]),
                # informativo: la UI non deve mai autorizzare sui role code
                "roles": breakdown["shelter_role_codes"],
                "is_technical_owner": ownership_service.is_active_owner(
                    user["id"], shelter_id
                ),
            },
        }
    except Exception as e:
        logger.error(e)
        return {"success": False, "error": format_error(e, token)}
