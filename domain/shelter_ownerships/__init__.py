"""OwnershipService: technical ownership of shelters.

Ownership answers "who is the technical owner of this shelter", nothing else:
it grants no permissions (that is RBAC's job) and holding SHELTER_ADMIN never
makes a user an owner. Proprietary operations require BOTH:

    authorization_service.authorize(..., permission="shelters.ownership.transfer", ...)
    ownership_service.require_active_owner(user_id=..., shelter_id=...)
"""
import repository.shelter_ownerships as ownerships_data
from api.errors import BadRequest, ForbiddenError
from utils.logger import logger


def _audit(action, actor_user_id, shelter_id, target_user_id=None, metadata=None):
    try:
        import repository.authorization as authz_data
        authz_data.write_audit_log(
            action=action,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            shelter_id=shelter_id,
            metadata=metadata,
        )
    except Exception as e:
        logger.error(f"failed to audit {action}: {e}")


def is_active_owner(user_id, shelter_id):
    return ownerships_data.get_active_ownership(user_id, shelter_id) is not None


def require_active_owner(user_id, shelter_id):
    if not is_active_owner(user_id, shelter_id):
        raise ForbiddenError("user is not an active owner of this shelter")


def list_active_owners(shelter_id):
    return ownerships_data.get_active_ownerships_for_shelter(shelter_id)


def list_owned_shelters(user_id):
    return ownerships_data.get_active_ownerships_for_user(user_id)


def add_owner(shelter_id, user_id, source, created_by_id=None, commit=True):
    """Idempotent; audits only when a new row is actually created."""
    ownership, created = ownerships_data.create_ownership(
        shelter_id=shelter_id,
        user_id=user_id,
        source=source,
        created_by_id=created_by_id,
        commit=commit,
    )
    if created:
        _audit(
            "SHELTER_OWNERSHIP_ADDED",
            actor_user_id=created_by_id,
            target_user_id=user_id,
            shelter_id=shelter_id,
            metadata={"source": source if isinstance(source, str) else source.name},
        )
    return ownership


def remove_owner(shelter_id, user_id, actor_user_id=None, status="ENDED", commit=True):
    """Ends the ACTIVE ownership; the last active owner cannot be removed."""
    ownership = ownerships_data.get_active_ownership(user_id, shelter_id)
    if ownership is None:
        raise BadRequest("user is not an active owner of this shelter")
    if ownerships_data.count_active_owners(shelter_id) <= 1:
        raise BadRequest("cannot remove the last active owner of a shelter")
    ended = ownerships_data.end_ownership(ownership["id"], status=status, commit=commit)
    _audit(
        "SHELTER_OWNERSHIP_REMOVED",
        actor_user_id=actor_user_id,
        target_user_id=user_id,
        shelter_id=shelter_id,
        metadata={"status": status},
    )
    return ended


def transfer_ownership(shelter_id, from_user_id, to_user_id, actor_user_id=None,
                       keep_previous_owner=False, source="OWNERSHIP_TRANSFER"):
    """Atomic swap: new owner in, previous owner out (unless kept). Uses a
    single transaction so the shelter can never observe zero owners."""
    from repository import db

    if from_user_id == to_user_id:
        raise BadRequest("cannot transfer ownership to the current owner")
    current = ownerships_data.get_active_ownership(from_user_id, shelter_id)
    if current is None:
        raise ForbiddenError("transferor is not an active owner of this shelter")
    try:
        ownerships_data.create_ownership(
            shelter_id=shelter_id,
            user_id=to_user_id,
            source=source,
            created_by_id=actor_user_id,
            commit=False,
        )
        if not keep_previous_owner:
            ownerships_data.end_ownership(current["id"], status="ENDED", commit=False)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"ownership transfer failed: {e}")
        raise e
    _audit(
        "SHELTER_OWNERSHIP_TRANSFERRED",
        actor_user_id=actor_user_id,
        target_user_id=to_user_id,
        shelter_id=shelter_id,
        metadata={"from_user_id": from_user_id, "kept_previous_owner": keep_previous_owner},
    )
    return ownerships_data.get_active_ownership(to_user_id, shelter_id)
