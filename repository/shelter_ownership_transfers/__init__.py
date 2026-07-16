import uuid
from datetime import datetime
from sqlalchemy import select, text, or_
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_ownership_transfers.models import ShelterOwnershipTransfer
from repository.query_builder import build_query, build_count
from utils.dates import utc_now

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def create_transfer(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        transfer = ShelterOwnershipTransfer(
            id=f"{uuid.uuid4()}",
            created_at=utc_now().strftime(DATE_FMT),
            shelter_id=data["shelter_id"],
            from_user_id=data["from_user_id"],
            to_user_id=data["to_user_id"],
            new_role_for_previous_owner=data.get("new_role_for_previous_owner"),
            status=data.get("status") or "PENDING",
        )
        db.session.add(transfer)
        db.session.commit()
        return transfer.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_transfer(id):
    model = ShelterOwnershipTransfer.query.get(id)
    if not model:
        raise NotFoundError(f"no shelter_ownership_transfer found with id: {id}")
    return model.to_dict()


def get_pending_for_shelter(shelter_id):
    models = db.session.query(ShelterOwnershipTransfer).filter(
        ShelterOwnershipTransfer.shelter_id == shelter_id,
        ShelterOwnershipTransfer.status == "PENDING",
    ).all()
    return [m.to_dict() for m in models]


def set_status(id, status, timestamp_field=None):
    try:
        model = db.session.query(ShelterOwnershipTransfer).filter(
            ShelterOwnershipTransfer.id == id
        ).first()
        if not model:
            raise NotFoundError(f"no shelter_ownership_transfer found with id: {id}")
        model.status = status
        if timestamp_field:
            setattr(model, timestamp_field, utc_now())
        db.session.commit()
        return model.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def list_for_user(user_id, pagination):
    page = pagination.get("page", 0)
    page_size = pagination.get("page_size", 20)
    query = db.session.query(ShelterOwnershipTransfer).filter(
        or_(
            ShelterOwnershipTransfer.from_user_id == user_id,
            ShelterOwnershipTransfer.to_user_id == user_id,
        )
    ).order_by(ShelterOwnershipTransfer.created_at.desc())
    total = query.count()
    rows = query.offset(page * page_size).limit(page_size).all()
    return [r.to_dict() for r in rows], total


def get_shelter_transfers(common_search):
    try:
        query = build_query(
            table="shelter_ownership_transfers",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterOwnershipTransfer).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_ownership_transfers", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e
