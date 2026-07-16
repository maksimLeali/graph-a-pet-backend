import uuid
from datetime import datetime
from repository import db
from api.errors import NotFoundError
from utils.logger import logger, stringify
from repository.shelter_invites.models import ShelterInvite
from utils.dates import utc_now

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def create_shelter_invite(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        invite = ShelterInvite(
            id=f"{uuid.uuid4()}",
            created_at=utc_now().strftime(DATE_FMT),
            shelter_id=data["shelter_id"],
            user_id=data["user_id"],
            role=data["role"],
            status=data.get("status") or "PENDING",
            invited_by_id=data.get("invited_by_id"),
        )
        db.session.add(invite)
        db.session.commit()
        return invite.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_invite(id):
    model = ShelterInvite.query.get(id)
    if not model:
        raise NotFoundError(f"no shelter_invite found with id: {id}")
    return model.to_dict()


def get_pending_for_user_shelter(user_id, shelter_id):
    from repository.shelter_invites.models import ShelterInviteStatus
    models = db.session.query(ShelterInvite).filter(
        ShelterInvite.user_id == user_id,
        ShelterInvite.shelter_id == shelter_id,
        ShelterInvite.status == ShelterInviteStatus.PENDING,
    ).all()
    return [m.to_dict() for m in models]


def set_status(id, status):
    try:
        model = db.session.query(ShelterInvite).filter(ShelterInvite.id == id).first()
        if not model:
            raise NotFoundError(f"no shelter_invite found with id: {id}")
        model.status = status
        db.session.commit()
        return model.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e
