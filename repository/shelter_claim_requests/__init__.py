import uuid
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_claim_requests.models import ShelterClaimRequest
from repository.query_builder import build_query, build_count
from utils.dates import utc_now

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def create_claim(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        claim = ShelterClaimRequest(
            id=f"{uuid.uuid4()}",
            created_at=utc_now().strftime(DATE_FMT),
            shelter_id=data["shelter_id"],
            requester_user_id=data["requester_user_id"],
            status=data.get("status") or "PENDING",
            proof_data=data.get("proof_data"),
            message=data.get("message"),
        )
        db.session.add(claim)
        db.session.commit()
        return claim.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_claim(id):
    model = ShelterClaimRequest.query.get(id)
    if not model:
        raise NotFoundError(f"no shelter_claim_request found with id: {id}")
    return model.to_dict()


def get_pending_for_user_shelter(user_id, shelter_id):
    models = db.session.query(ShelterClaimRequest).filter(
        ShelterClaimRequest.requester_user_id == user_id,
        ShelterClaimRequest.shelter_id == shelter_id,
        ShelterClaimRequest.status == "PENDING",
    ).all()
    return [m.to_dict() for m in models]


def set_status(id, status):
    try:
        model = db.session.query(ShelterClaimRequest).filter(
            ShelterClaimRequest.id == id
        ).first()
        if not model:
            raise NotFoundError(f"no shelter_claim_request found with id: {id}")
        model.status = status
        db.session.commit()
        return model.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def resolve_claim(id, status, reviewed_by, decision_note):
    """Admin decision (approve/reject): status + review metadata in one go."""
    try:
        model = db.session.query(ShelterClaimRequest).filter(
            ShelterClaimRequest.id == id
        ).first()
        if not model:
            raise NotFoundError(f"no shelter_claim_request found with id: {id}")
        model.status = status
        model.reviewed_by = reviewed_by
        model.reviewed_at = utc_now()
        if decision_note is not None:
            model.decision_note = decision_note
        db.session.commit()
        return model.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def list_for_user(user_id, pagination):
    page = pagination.get("page", 0)
    page_size = pagination.get("page_size", 20)
    query = db.session.query(ShelterClaimRequest).filter(
        ShelterClaimRequest.requester_user_id == user_id
    ).order_by(ShelterClaimRequest.created_at.desc())
    total = query.count()
    rows = query.offset(page * page_size).limit(page_size).all()
    return [r.to_dict() for r in rows], total


def get_shelter_claims(common_search):
    try:
        query = build_query(
            table="shelter_claim_requests",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterClaimRequest).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_claim_requests", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e
