import uuid
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_zones.models import ShelterZone
from repository.query_builder import build_query, build_count
from utils.dates import utc_now


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def create_shelter_zone(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = utc_now()
        zone = ShelterZone(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            map_id=data["map_id"],
            name=data.get("name"),
            x=data.get("x"),
            y=data.get("y"),
            width=data.get("width"),
            height=data.get("height"),
            color=data.get("color"),
        )
        db.session.add(zone)
        db.session.commit()
        return zone.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_zone(id, data):
    logger.repository(f"id: {id}\ndata: {stringify(data)}")
    try:
        query = db.session.query(ShelterZone).filter(ShelterZone.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_zone found with id: {id}")
        old = query.first().to_dict()
        query.update(dict(data))
        db.session.commit()
        return {**old, **query.first().to_dict()}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_zone(id):
    logger.repository(f"id: {id}")
    try:
        model = ShelterZone.query.get(id)
        if not model:
            raise NotFoundError(f"no shelter_zone found with id: {id}")
        return model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def get_zones_by_map(map_id):
    models = db.session.query(ShelterZone).filter(ShelterZone.map_id == map_id).all()
    return [m.to_dict() for m in models]


def get_shelter_zones(common_search):
    try:
        query = build_query(
            table="shelter_zones",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterZone).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_zones", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_zone(id):
    logger.repository(f"id: {id} remove")
    try:
        query = db.session.query(ShelterZone).filter(ShelterZone.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_zone found with id: {id}")
        query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e
