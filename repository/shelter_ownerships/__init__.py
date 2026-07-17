import uuid

from repository import db
from repository.shelter_ownerships.models import (
    ShelterOwnership,
    ShelterOwnershipStatus,
    ShelterOwnershipSource,
)
from utils.dates import utc_now
from utils.logger import logger


def _new_id():
    return f"{uuid.uuid4()}"


def get_active_ownership(user_id, shelter_id):
    model = db.session.query(ShelterOwnership).filter(
        ShelterOwnership.user_id == user_id,
        ShelterOwnership.shelter_id == shelter_id,
        ShelterOwnership.status == ShelterOwnershipStatus.ACTIVE,
    ).first()
    return model.to_dict() if model else None


def get_active_ownerships_for_shelter(shelter_id):
    models = db.session.query(ShelterOwnership).filter(
        ShelterOwnership.shelter_id == shelter_id,
        ShelterOwnership.status == ShelterOwnershipStatus.ACTIVE,
    ).all()
    return [m.to_dict() for m in models]


def get_active_ownerships_for_user(user_id):
    models = db.session.query(ShelterOwnership).filter(
        ShelterOwnership.user_id == user_id,
        ShelterOwnership.status == ShelterOwnershipStatus.ACTIVE,
    ).all()
    return [m.to_dict() for m in models]


def count_active_owners(shelter_id):
    return db.session.query(ShelterOwnership).filter(
        ShelterOwnership.shelter_id == shelter_id,
        ShelterOwnership.status == ShelterOwnershipStatus.ACTIVE,
    ).count()


def create_ownership(shelter_id, user_id, source, created_by_id=None, commit=True):
    """Idempotent: an existing ACTIVE row for (shelter, user) is returned as-is."""
    existing = get_active_ownership(user_id, shelter_id)
    if existing:
        return existing, False
    model = ShelterOwnership(
        id=_new_id(),
        shelter_id=shelter_id,
        user_id=user_id,
        status=ShelterOwnershipStatus.ACTIVE,
        source=ShelterOwnershipSource[source] if isinstance(source, str) else source,
        created_by_id=created_by_id,
        created_at=utc_now(),
    )
    db.session.add(model)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return model.to_dict(), True


def end_ownership(ownership_id, status="ENDED", commit=True):
    model = db.session.query(ShelterOwnership).filter(
        ShelterOwnership.id == ownership_id,
    ).first()
    if not model:
        return None
    model.status = ShelterOwnershipStatus[status]
    model.ended_at = utc_now()
    model.updated_at = utc_now()
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return model.to_dict()
