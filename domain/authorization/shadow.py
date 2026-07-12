"""Shadow mode: compare legacy role decisions with RBAC decisions.

Hooked into the legacy authorization helpers (api.middlewares /
api.permissions). It NEVER grants or denies anything — it only logs
divergences so missing mappings surface before each module is migrated.

Enable/disable with config.yml:

    rbac:
      shadow_mode: true

Defaults to enabled; every failure inside the comparison is swallowed.
"""
from config import cfg
from utils.logger import logger
from domain.authorization.catalog import ShelterPermissions

# Marker permission per legacy tier: the cheapest single permission whose
# presence proves the RBAC side grants at least that legacy level.
LEGACY_TIER_MARKER = {
    "VOLUNTEER": ShelterPermissions.READ,
    "STAFF": ShelterPermissions.INVENTORY_CONSUME,
    "MANAGER": ShelterPermissions.BOXES_MANAGE,
    "OWNER": ShelterPermissions.ROLES_MANAGE,
}

_warned_unavailable = False


def _enabled():
    return bool(cfg.get("rbac", {}).get("shadow_mode", True))


def compare_shelter_decision(user_id, shelter_id, legacy_required_role, legacy_allowed):
    """Log LEGACY_ALLOWED_RBAC_DENIED / LEGACY_DENIED_RBAC_ALLOWED divergences
    for an assert_shelter_role-style check. Grants nothing."""
    global _warned_unavailable
    if not _enabled():
        return
    try:
        from domain.authorization import authorization_service
        marker = LEGACY_TIER_MARKER.get((legacy_required_role or "").upper())
        if marker is None:
            return
        rbac_allowed = authorization_service.can(user_id, marker, shelter_id=shelter_id)
        if legacy_allowed and not rbac_allowed:
            logger.warning(
                "shadow_authorization_mismatch LEGACY_ALLOWED_RBAC_DENIED "
                f"user={user_id} shelter={shelter_id} legacy_role={legacy_required_role} marker={marker}"
            )
        elif not legacy_allowed and rbac_allowed:
            logger.warning(
                "shadow_authorization_mismatch LEGACY_DENIED_RBAC_ALLOWED "
                f"user={user_id} shelter={shelter_id} legacy_role={legacy_required_role} marker={marker}"
            )
    except Exception as e:
        if not _warned_unavailable:
            logger.warning(f"rbac shadow mode unavailable (tables missing?): {e}")
            _warned_unavailable = True
