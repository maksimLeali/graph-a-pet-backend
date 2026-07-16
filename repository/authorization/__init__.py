import uuid
from datetime import datetime

from repository import db
from utils.logger import logger, stringify

# ensure FK targets (users, shelters) are registered in the shared metadata
# even when this package is imported standalone (seed/backfill scripts, tests)
import repository.users.models  # noqa: F401
import repository.shelters.models  # noqa: F401
# User declares relationships to Ownership and ShelterRole by class name;
# they must be importable before the mapper configures
import repository.ownerships.models  # noqa: F401
import repository.shelter_roles.models  # noqa: F401
from utils.dates import utc_now
from repository.authorization.models import (
    Permission,
    Role,
    RolePermission,
    UserRoleAssignment,
    ShelterMembership,
    AuthorizationAuditLog,
    RbacScopeType,
    UserRoleStatus,
    ShelterMembershipStatus,
    ShelterMembershipSource,
)

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _now():
    return utc_now()


def _new_id():
    return f"{uuid.uuid4()}"


# ---------------------------------------------------------------------------
# Read side used by the AuthorizationService
# ---------------------------------------------------------------------------

def get_active_assignments(user_id, shelter_id=None):
    """All ACTIVE role assignments applying to (user, shelter): platform-scoped
    ones (shelter_id NULL) plus, when shelter_id is given, that shelter's.
    Time-window (valid_from/valid_until) filtering happens in the domain
    service so it stays unit-testable."""
    q = db.session.query(UserRoleAssignment, Role).join(
        Role, UserRoleAssignment.role_id == Role.id
    ).filter(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.status == UserRoleStatus.ACTIVE,
        Role.archived_at.is_(None),
    )
    if shelter_id is None:
        q = q.filter(UserRoleAssignment.shelter_id.is_(None))
    else:
        q = q.filter(
            db.or_(
                UserRoleAssignment.shelter_id.is_(None),
                UserRoleAssignment.shelter_id == shelter_id,
            )
        )
    return [
        {**assignment.to_dict(), "role": role.to_dict()}
        for assignment, role in q.all()
    ]


def get_permission_keys_for_roles(role_ids):
    if not role_ids:
        return set()
    rows = db.session.query(Permission.key).join(
        RolePermission, RolePermission.permission_id == Permission.id
    ).filter(RolePermission.role_id.in_(role_ids)).all()
    return {r[0] for r in rows}


def get_membership(user_id, shelter_id):
    m = db.session.query(ShelterMembership).filter(
        ShelterMembership.user_id == user_id,
        ShelterMembership.shelter_id == shelter_id,
    ).first()
    return m.to_dict() if m else None


def get_all_permission_keys():
    return {r[0] for r in db.session.query(Permission.key).all()}


def create_custom_role(code, name, description, scope_type):
    existing = db.session.query(Role).filter(Role.code == code).first()
    if existing:
        raise ValueError(f"role with code '{code}' already exists")
    model = Role(
        id=_new_id(),
        code=code.upper(),
        name=name,
        description=description or None,
        scope_type=RbacScopeType[scope_type],
        is_system=False,
        is_assignable=True,
        grants_all_permissions=False,
        created_at=_now(),
    )
    db.session.add(model)
    db.session.flush()
    return model.to_dict()


def archive_role(role_id):
    model = db.session.query(Role).filter(
        Role.id == role_id,
        Role.is_system.is_(False),
        Role.archived_at.is_(None),
    ).first()
    if not model:
        raise ValueError("role not found, is a system role, or already archived")
    model.archived_at = _now()
    model.updated_at = _now()
    db.session.flush()
    return model.to_dict()


def list_roles_with_permissions():
    roles = db.session.query(Role).filter(Role.archived_at.is_(None)).order_by(Role.code).all()
    result = []
    for role in roles:
        perm_keys = sorted(get_permission_keys_for_roles([role.id]))
        r = role.to_dict()
        r["permissions"] = perm_keys
        result.append(r)
    return result


def list_user_role_assignments(user_id):
    rows = db.session.query(UserRoleAssignment, Role).join(
        Role, UserRoleAssignment.role_id == Role.id
    ).filter(
        UserRoleAssignment.user_id == user_id,
        Role.archived_at.is_(None),
    ).order_by(UserRoleAssignment.created_at).all()
    return [
        {**assignment.to_dict(), "role": role.to_dict()}
        for assignment, role in rows
    ]


def get_role(role_id):
    role = db.session.query(Role).filter(Role.id == role_id).first()
    return role.to_dict() if role else None


def get_role_by_code(code):
    role = db.session.query(Role).filter(Role.code == code).first()
    return role.to_dict() if role else None


# ---------------------------------------------------------------------------
# Seed / backfill helpers (idempotent upserts)
# ---------------------------------------------------------------------------

def upsert_permission(meta):
    """Insert or update a permission by key. Returns its dict."""
    model = db.session.query(Permission).filter(Permission.key == meta["key"]).first()
    if model is None:
        model = Permission(
            id=_new_id(),
            key=meta["key"],
            created_at=_now(),
        )
        db.session.add(model)
    model.domain = meta["domain"]
    model.action = meta["action"]
    model.description = meta.get("description") or model.description
    model.scope_type = RbacScopeType[meta["scope_type"]]
    model.risk_level = meta.get("risk_level", "LOW")
    model.updated_at = _now()
    db.session.flush()
    return model.to_dict()


def upsert_system_role(definition):
    """Insert or update a system role by code. Returns its dict."""
    model = db.session.query(Role).filter(Role.code == definition["code"]).first()
    if model is None:
        model = Role(id=_new_id(), code=definition["code"], created_at=_now())
        db.session.add(model)
    model.name = definition["name"]
    model.description = definition.get("description")
    model.scope_type = RbacScopeType[definition["scope_type"]]
    model.owner_shelter_id = None
    model.is_system = True
    model.is_assignable = True
    model.grants_all_permissions = bool(definition.get("grants_all_permissions"))
    model.archived_at = None
    model.updated_at = _now()
    db.session.flush()
    return model.to_dict()


def sync_role_permissions(role_id, permission_keys):
    """Make role_permissions for role_id exactly match permission_keys.
    Idempotent: adds missing links, removes stale ones."""
    wanted = db.session.query(Permission).filter(Permission.key.in_(permission_keys)).all() if permission_keys else []
    wanted_by_id = {p.id for p in wanted}
    if permission_keys and len(wanted) != len(set(permission_keys)):
        found = {p.key for p in wanted}
        missing = set(permission_keys) - found
        raise ValueError(f"permissions missing from catalog table: {missing}")

    existing = db.session.query(RolePermission).filter(RolePermission.role_id == role_id).all()
    existing_by_pid = {rp.permission_id: rp for rp in existing}

    added, removed = 0, 0
    for pid in wanted_by_id - set(existing_by_pid):
        db.session.add(RolePermission(
            id=_new_id(), role_id=role_id, permission_id=pid, created_at=_now(),
        ))
        added += 1
    for pid in set(existing_by_pid) - wanted_by_id:
        db.session.delete(existing_by_pid[pid])
        removed += 1
    db.session.flush()
    return added, removed


def ensure_membership(shelter_id, user_id, source, status=ShelterMembershipStatus.ACTIVE):
    """Create the membership if absent; never duplicates (unique shelter+user)."""
    existing = db.session.query(ShelterMembership).filter(
        ShelterMembership.shelter_id == shelter_id,
        ShelterMembership.user_id == user_id,
    ).first()
    if existing:
        return existing.to_dict(), False
    model = ShelterMembership(
        id=_new_id(),
        shelter_id=shelter_id,
        user_id=user_id,
        status=status,
        source=source if isinstance(source, ShelterMembershipSource) else ShelterMembershipSource[source],
        joined_at=_now(),
        created_at=_now(),
    )
    db.session.add(model)
    db.session.flush()
    return model.to_dict(), True


def admin_assign_user_role(user_id, role_id, shelter_id=None, assigned_by_id=None):
    """Explicit admin assignment. Unlike ensure_user_role (backfill-safe),
    this DOES reactivate a previously revoked/suspended/expired row — the
    admin is deliberately re-granting the role."""
    q = db.session.query(UserRoleAssignment).filter(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.role_id == role_id,
    )
    if shelter_id is None:
        q = q.filter(UserRoleAssignment.shelter_id.is_(None))
    else:
        q = q.filter(UserRoleAssignment.shelter_id == shelter_id)
    existing = q.first()
    if existing:
        existing.status = UserRoleStatus.ACTIVE
        existing.revoked_at = None
        existing.revoked_by_id = None
        existing.assigned_by_id = assigned_by_id
        existing.updated_at = _now()
        db.session.flush()
        return existing.to_dict(), False
    model = UserRoleAssignment(
        id=_new_id(),
        user_id=user_id,
        role_id=role_id,
        shelter_id=shelter_id,
        status=UserRoleStatus.ACTIVE,
        assigned_by_id=assigned_by_id,
        created_at=_now(),
    )
    db.session.add(model)
    db.session.flush()
    return model.to_dict(), True


def revoke_user_role_assignment(assignment_id, revoked_by_id):
    model = db.session.query(UserRoleAssignment).filter(
        UserRoleAssignment.id == assignment_id,
    ).first()
    if not model:
        raise ValueError(f"no user role assignment found with id {assignment_id}")
    model.status = UserRoleStatus.REVOKED
    model.revoked_at = _now()
    model.revoked_by_id = revoked_by_id
    model.updated_at = _now()
    db.session.flush()
    return model.to_dict()


def ensure_user_role(user_id, role_id, shelter_id=None, assigned_by_id=None):
    """Create the assignment if no row exists for (user, role, shelter);
    reactivation of revoked rows is intentionally NOT done here (backfill
    must not resurrect revocations)."""
    q = db.session.query(UserRoleAssignment).filter(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.role_id == role_id,
    )
    if shelter_id is None:
        q = q.filter(UserRoleAssignment.shelter_id.is_(None))
    else:
        q = q.filter(UserRoleAssignment.shelter_id == shelter_id)
    existing = q.first()
    if existing:
        return existing.to_dict(), False
    model = UserRoleAssignment(
        id=_new_id(),
        user_id=user_id,
        role_id=role_id,
        shelter_id=shelter_id,
        status=UserRoleStatus.ACTIVE,
        assigned_by_id=assigned_by_id,
        created_at=_now(),
    )
    db.session.add(model)
    db.session.flush()
    return model.to_dict(), True


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def write_audit_log(action, actor_user_id=None, target_user_id=None, shelter_id=None,
                    role_id=None, permission_id=None, before_data=None, after_data=None,
                    request_id=None, metadata=None):
    try:
        model = AuthorizationAuditLog(
            id=_new_id(),
            action=action,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            shelter_id=shelter_id,
            role_id=role_id,
            permission_id=permission_id,
            before_data=before_data,
            after_data=after_data,
            request_id=request_id,
            meta=metadata,
            created_at=_now(),
        )
        db.session.add(model)
        db.session.flush()
        return model.to_dict()
    except Exception as e:
        # auditing must never take the main operation down
        logger.error(f"audit log write failed: {e}")
        return None
