import uuid

from api.errors import NotFoundError
from repository import db
from repository.shelter_join_requests.models import ShelterJoinRequest
from utils.dates import utc_now
from utils.logger import logger, stringify


def create_join_request(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        join_request = ShelterJoinRequest(
            id=f"{uuid.uuid4()}",
            created_at=utc_now(),
            shelter_id=data["shelter_id"],
            user_id=data["user_id"],
            status=data.get("status") or "PENDING",
            message=data.get("message"),
        )
        db.session.add(join_request)
        db.session.commit()
        return join_request.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_join_request(id):
    model = ShelterJoinRequest.query.get(id)
    if not model:
        raise NotFoundError(f"no shelter_join_request found with id: {id}")
    return model.to_dict()


def get_pending_for_user_shelter(user_id, shelter_id):
    models = db.session.query(ShelterJoinRequest).filter(
        ShelterJoinRequest.user_id == user_id,
        ShelterJoinRequest.shelter_id == shelter_id,
        ShelterJoinRequest.status == "PENDING",
    ).all()
    return [m.to_dict() for m in models]


def list_for_shelter(shelter_id, status=None):
    query = db.session.query(ShelterJoinRequest).filter(
        ShelterJoinRequest.shelter_id == shelter_id,
    )
    if status:
        query = query.filter(ShelterJoinRequest.status == status)
    models = query.order_by(ShelterJoinRequest.created_at.desc()).all()
    return [m.to_dict() for m in models]


def set_status(id, status, reviewed_by=None):
    try:
        model = db.session.query(ShelterJoinRequest).filter(
            ShelterJoinRequest.id == id
        ).first()
        if not model:
            raise NotFoundError(f"no shelter_join_request found with id: {id}")
        model.status = status
        if reviewed_by is not None:
            model.reviewed_by = reviewed_by
            model.reviewed_at = utc_now()
        db.session.commit()
        return model.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e
