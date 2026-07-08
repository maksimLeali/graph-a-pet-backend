import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_walks.models import ShelterWalk, ShelterWalkStatus
from repository.shelter_pets.models import ShelterPet
from repository.query_builder import build_query, build_count


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.strptime(value, DATE_FMT)


def create_shelter_walk(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        walk = ShelterWalk(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            shelter_pet_id=data["shelter_pet_id"],
            walker_id=data["walker_id"],
            status=data.get("status") or ShelterWalkStatus.PLANNED.name,
            scheduled_at=_parse_dt(data.get("scheduled_at")),
            notes=data.get("notes"),
        )
        db.session.add(walk)
        db.session.commit()
        return walk.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_walk(id, data):
    logger.repository(f"id: {id}\ndata: {stringify(data)}")
    try:
        query = db.session.query(ShelterWalk).filter(ShelterWalk.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_walk found with id: {id}")
        old = query.first().to_dict()
        payload = dict(data)
        for k in ("scheduled_at", "started_at", "ended_at"):
            if k in payload:
                payload[k] = _parse_dt(payload.get(k))
        query.update(payload)
        db.session.commit()
        return {**old, **query.first().to_dict()}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_walk(id):
    logger.repository(f"id: {id}")
    try:
        model = ShelterWalk.query.get(id)
        if not model:
            raise NotFoundError(f"no shelter_walk found with id: {id}")
        return model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_walks(common_search):
    try:
        query = build_query(
            table="shelter_walks",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterWalk).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_walks", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_walk(id):
    logger.repository(f"id: {id} remove")
    try:
        query = db.session.query(ShelterWalk).filter(ShelterWalk.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_walk found with id: {id}")
        query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def count_completed_between(shelter_id, start, end):
    return db.session.query(ShelterWalk).join(
        ShelterPet, ShelterWalk.shelter_pet_id == ShelterPet.id
    ).filter(
        ShelterPet.shelter_id == shelter_id,
        ShelterWalk.status == ShelterWalkStatus.COMPLETED,
        ShelterWalk.ended_at >= start,
        ShelterWalk.ended_at < end,
    ).count()


def count_planned_between(shelter_id, start, end):
    return db.session.query(ShelterWalk).join(
        ShelterPet, ShelterWalk.shelter_pet_id == ShelterPet.id
    ).filter(
        ShelterPet.shelter_id == shelter_id,
        ShelterWalk.status == ShelterWalkStatus.PLANNED,
        ShelterWalk.scheduled_at >= start,
        ShelterWalk.scheduled_at < end,
    ).count()


def count_in_progress(shelter_id):
    return db.session.query(ShelterWalk).join(
        ShelterPet, ShelterWalk.shelter_pet_id == ShelterPet.id
    ).filter(
        ShelterPet.shelter_id == shelter_id,
        ShelterWalk.status == ShelterWalkStatus.IN_PROGRESS,
    ).count()


def get_pets_needing_walk(shelter_id, hours=24):
    """Shelter pets senza una ShelterWalk COMPLETED nelle ultime <hours> ore."""
    logger.repository(f"shelter_id: {shelter_id} hours: {hours}")
    try:
        cutoff = datetime.today() - timedelta(hours=hours)
        pets = db.session.query(ShelterPet).filter(
            ShelterPet.shelter_id == shelter_id
        ).all()
        pet_ids = [p.id for p in pets]
        if not pet_ids:
            return []
        recent = db.session.query(ShelterWalk).filter(
            ShelterWalk.shelter_pet_id.in_(pet_ids),
            ShelterWalk.status == ShelterWalkStatus.COMPLETED,
            ShelterWalk.ended_at >= cutoff,
        ).all()
        walked = {w.shelter_pet_id for w in recent}
        return [p.to_dict() for p in pets if p.id not in walked]
    except Exception as e:
        logger.error(e)
        raise e
