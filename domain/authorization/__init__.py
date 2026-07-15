"""AuthorizationService: permission-first RBAC decisions.

Application code never checks role names; it asks:

    authorization_service.authorize(
        user_id=user_id,
        permission=ShelterPermissions.TASKS_CREATE,
        shelter_id=shelter_id,
    )

Default is DENY: no assignment, no permission, wrong scope, inactive
membership or expired role all fail closed.

RBAC only answers "may this user perform this action in this scope".
Entity-tenant checks (task.shelter_id == shelter_id) and domain rules stay in
their domain services.
"""
from datetime import datetime

from flask import g, has_request_context

from api.errors import (
    AuthenticationError,
    ForbiddenError,
    InvalidAuthorizationScopeError,
    MembershipNotActiveError,
)
from domain.authorization.catalog import (
    SCOPE_PLATFORM,
    SCOPE_SHELTER,
    HIGH_RISK,
    assert_valid_permission,
)
from utils.logger import logger


def _default_loader():
    # late import: repository initialises the flask app/db at import time
    import repository.authorization as authz_data
    return authz_data


class AuthorizationService:
    """`loader` is any object exposing get_active_assignments,
    get_permission_keys_for_roles, get_membership and write_audit_log —
    injectable for pure unit tests."""

    def __init__(self, loader=None):
        self._loader = loader

    @property
    def loader(self):
        return self._loader or _default_loader()

    # -- public API ---------------------------------------------------------

    def can(self, user_id, permission, shelter_id=None, now=None):
        """True when user holds `permission` in the requested scope."""
        try:
            self.authorize(user_id, permission, shelter_id=shelter_id, now=now)
            return True
        except (ForbiddenError, MembershipNotActiveError, AuthenticationError):
            return False

    def authorize(self, user_id, permission, shelter_id=None, now=None):
        """Raise unless user holds `permission` in the requested scope.
        Returns the effective permission set on success."""
        assert_valid_permission(permission)
        if not user_id:
            raise AuthenticationError("unauthorized")

        self._validate_scope(permission, shelter_id)

        context = self._load_context(user_id, shelter_id)
        effective = self._effective_permissions(context, shelter_id, now=now)

        logger.critical(f"authorization_check user={user_id} permission={permission} shelter={shelter_id} effective={effective}")

        if permission in effective:
            return effective

        if context["membership_blocked"]:
            raise MembershipNotActiveError("membership is not active on this shelter")

        if permission in HIGH_RISK:
            self._audit_sensitive_denial(user_id, permission, shelter_id)
        logger.warning(
            f"authorization_denied user={user_id} permission={permission} shelter={shelter_id}"
        )
        raise ForbiddenError(f"missing permission: {permission}")

    def effective_permissions(self, user_id, shelter_id=None, now=None):
        """Union of permission keys granted by the user's active roles in the
        scope. Used by the myShelterAuthorization query."""
        if not user_id:
            return set()
        context = self._load_context(user_id, shelter_id)
        return self._effective_permissions(context, shelter_id, now=now)

    def membership_status(self, user_id, shelter_id):
        context = self._load_context(user_id, shelter_id)
        membership = context["membership"]
        return membership["status"] if membership else None

    # -- internals ----------------------------------------------------------

    def _validate_scope(self, permission, shelter_id):
        scope = SCOPE_PLATFORM if permission.startswith("platform.") else SCOPE_SHELTER
        if scope == SCOPE_SHELTER and not shelter_id:
            raise InvalidAuthorizationScopeError(
                f"permission {permission} requires a shelter scope"
            )
        if scope == SCOPE_PLATFORM and shelter_id:
            raise InvalidAuthorizationScopeError(
                f"permission {permission} is platform-scoped, got shelter_id"
            )

    def _load_context(self, user_id, shelter_id):
        """Assignments + membership for (user, shelter), cached per request."""
        cache_key = f"rbac:{user_id}:{shelter_id}"
        if has_request_context():
            cache = getattr(g, "_rbac_cache", None)
            if cache is None:
                cache = g._rbac_cache = {}
            if cache_key in cache:
                return cache[cache_key]

        assignments = self.loader.get_active_assignments(user_id, shelter_id)
        membership = (
            self.loader.get_membership(user_id, shelter_id) if shelter_id else None
        )
        membership_blocked = bool(membership) and membership["status"] != "ACTIVE"

        context = {
            "user_id": user_id,
            "shelter_id": shelter_id,
            "assignments": assignments,
            "membership": membership,
            "membership_blocked": membership_blocked,
        }
        if has_request_context():
            g._rbac_cache[cache_key] = context
        return context

    def _effective_permissions(self, context, shelter_id, now=None):
        now = now or datetime.utcnow()
        role_ids = []
        grants_all_scopes = set()

        for assignment in context["assignments"]:            
            if not self._assignment_active(assignment, now):
                continue
            role = assignment["role"]
            is_platform_role = assignment["shelter_id"] is None

            # A shelter-scoped assignment only counts with a usable membership:
            # a non-ACTIVE membership blocks it; a missing membership is
            # tolerated for legacy rows created before RBAC (logged).
            if not is_platform_role:
                if context["membership_blocked"]:
                    continue
                if context["membership"] is None:
                    logger.warning(
                        f"legacy shelter role without membership: user={assignment['user_id']} "
                        f"shelter={assignment['shelter_id']} role={role['code']}"
                    )
            logger.critical(f'have all permissions? {role.get("grants_all_permissions")}')
            if role.get("grants_all_permissions"):
                if role["scope_type"] == SCOPE_PLATFORM:
                    grants_all_scopes.add(SCOPE_PLATFORM)
                    grants_all_scopes.add(SCOPE_SHELTER)
                elif assignment["shelter_id"] == shelter_id:
                    # shelter-scoped grants-all only covers its own shelter
                    grants_all_scopes.add(SCOPE_SHELTER)
                continue
            role_ids.append(role["id"])

        effective = set(self.loader.get_permission_keys_for_roles(role_ids))
        if grants_all_scopes:
            from domain.authorization.catalog import ALL_PERMISSION_KEYS
            for key in ALL_PERMISSION_KEYS:
                key_scope = SCOPE_PLATFORM if key.startswith("platform.") else SCOPE_SHELTER
                if key_scope in grants_all_scopes:
                    effective.add(key)
        return effective

    @staticmethod
    def _assignment_active(assignment, now):
        if assignment["status"] != "ACTIVE":
            return False
        valid_from = assignment.get("valid_from")
        valid_until = assignment.get("valid_until")
        try:
            if valid_from and datetime.fromisoformat(str(valid_from)) > now:
                return False
            if valid_until and datetime.fromisoformat(str(valid_until)) <= now:
                return False
        except ValueError:
            logger.error(f"unparsable validity window on user_role {assignment.get('id')}")
            return False
        return True

    def _audit_sensitive_denial(self, user_id, permission, shelter_id):
        try:
            self.loader.write_audit_log(
                action="SENSITIVE_AUTHORIZATION_DENIED",
                actor_user_id=user_id,
                shelter_id=shelter_id,
                metadata={"permission": permission},
            )
            from repository import db
            db.session.commit()
        except Exception as e:
            logger.error(f"failed to audit sensitive denial: {e}")


authorization_service = AuthorizationService()


def invalidate_request_cache():
    """Call after any role/membership mutation inside a request."""
    if has_request_context() and hasattr(g, "_rbac_cache"):
        g._rbac_cache = {}
