import uuid
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_box_occupancies.models import ShelterBoxOccupancy
from repository.query_builder import build_query, build_count


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _now():
    return datetime.today().strftime(DATE_FMT)


def get_active_occupancy_for_pet(shelter_pet_id):
    model = db.session.query(ShelterBoxOccupancy).filter(
        ShelterBoxOccupancy.shelter_pet_id == shelter_pet_id,
        ShelterBoxOccupancy.exited_at.is_(None),
    ).first()
    return model.to_dict() if model else None


def get_active_occupancies_for_box(box_id):
    models = db.session.query(ShelterBoxOccupancy).filter(
        ShelterBoxOccupancy.box_id == box_id,
        ShelterBoxOccupancy.exited_at.is_(None),
    ).all()
    return [m.to_dict() for m in models]


def count_active_for_box(box_id):
    return db.session.query(ShelterBoxOccupancy).filter(
        ShelterBoxOccupancy.box_id == box_id,
        ShelterBoxOccupancy.exited_at.is_(None),
    ).count()


def create_occupancy(box_id, shelter_pet_id, moved_by_id=None, reason=None):
    logger.repository(f"box: {box_id} pet: {shelter_pet_id}")
    try:
        occ = ShelterBoxOccupancy(
            id=f"{uuid.uuid4()}",
            created_at=_now(),
            box_id=box_id,
            shelter_pet_id=shelter_pet_id,
            entered_at=datetime.today(),
            moved_by_id=moved_by_id,
            reason=reason,
        )
        db.session.add(occ)
        db.session.commit()
        return occ.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def close_occupancy(occupancy_id, moved_by_id=None, reason=None):
    logger.repository(f"occupancy: {occupancy_id} close")
    try:
        query = db.session.query(ShelterBoxOccupancy).filter(
            ShelterBoxOccupancy.id == occupancy_id
        )
        model = query.first()
        if not model:
            raise NotFoundError(f"no occupancy found with id: {occupancy_id}")
        if model.exited_at is not None:
            raise BadRequest("occupancy already closed")
        payload = {"exited_at": datetime.today()}
        if moved_by_id is not None:
            payload["moved_by_id"] = moved_by_id
        if reason is not None:
            payload["reason"] = reason
        query.update(payload)
        db.session.commit()
        return query.first().to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def move_pet_between_boxes(shelter_pet_id, to_box_id, moved_by_id=None, reason=None):
    """Atomico: chiude l'occupancy attiva del pet e ne apre una sul box destinazione."""
    logger.repository(f"move pet {shelter_pet_id} -> box {to_box_id}")
    try:
        active = db.session.query(ShelterBoxOccupancy).filter(
            ShelterBoxOccupancy.shelter_pet_id == shelter_pet_id,
            ShelterBoxOccupancy.exited_at.is_(None),
        ).first()
        if active is not None:
            active.exited_at = datetime.today()
            if moved_by_id is not None:
                active.moved_by_id = moved_by_id
            if reason is not None:
                active.reason = reason
        new_occ = ShelterBoxOccupancy(
            id=f"{uuid.uuid4()}",
            created_at=_now(),
            box_id=to_box_id,
            shelter_pet_id=shelter_pet_id,
            entered_at=datetime.today(),
            moved_by_id=moved_by_id,
            reason=reason,
        )
        db.session.add(new_occ)
        db.session.commit()
        return new_occ.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_occupancy(id):
    model = ShelterBoxOccupancy.query.get(id)
    if not model:
        raise NotFoundError(f"no occupancy found with id: {id}")
    return model.to_dict()


def get_occupancies_for_box(box_id):
    models = db.session.query(ShelterBoxOccupancy).filter(
        ShelterBoxOccupancy.box_id == box_id
    ).order_by(ShelterBoxOccupancy.entered_at.desc()).all()
    return [m.to_dict() for m in models]


def get_occupancies(common_search):
    try:
        query = build_query(
            table="shelter_box_occupancies",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterBoxOccupancy).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_box_occupancies", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e
