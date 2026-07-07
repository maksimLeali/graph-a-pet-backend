import uuid
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_boxes.models import ShelterBox
from repository.query_builder import build_query, build_count


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.strptime(value, DATE_FMT)


def create_shelter_box(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        box = ShelterBox(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            map_id=data["map_id"],
            zone_id=data["zone_id"],
            area_id=data.get("area_id"),
            label=data["label"],
            x=data.get("x"),
            y=data.get("y"),
            width=data.get("width"),
            height=data.get("height"),
            rotation=data.get("rotation") if data.get("rotation") is not None else 0,
            capacity=data.get("capacity") if data.get("capacity") is not None else 1,
            notes=data.get("notes"),
        )
        db.session.add(box)
        db.session.commit()
        return box.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_box(id, data):
    logger.repository(f"id: {id}\ndata: {stringify(data)}")
    try:
        query = db.session.query(ShelterBox).filter(ShelterBox.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_box found with id: {id}")
        old = query.first().to_dict()
        payload = dict(data)
        if "last_cleaned_at" in payload:
            payload["last_cleaned_at"] = _parse_dt(payload.get("last_cleaned_at"))
        query.update(payload)
        db.session.commit()
        return {**old, **query.first().to_dict()}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_box(id):
    logger.repository(f"id: {id}")
    try:
        model = ShelterBox.query.get(id)
        if not model:
            raise NotFoundError(f"no shelter_box found with id: {id}")
        return model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def get_boxes_by_map(map_id):
    logger.repository(f"map_id: {map_id}")
    try:
        models = db.session.query(ShelterBox).filter(ShelterBox.map_id == map_id).all()
        return [m.to_dict() for m in models]
    except Exception as e:
        logger.error(e)
        raise e


def get_boxes_by_area(area_id):
    logger.repository(f"area_id: {area_id}")
    try:
        models = db.session.query(ShelterBox).filter(ShelterBox.area_id == area_id).all()
        return [m.to_dict() for m in models]
    except Exception as e:
        logger.error(e)
        raise e


def get_boxes_by_zone(zone_id):
    logger.repository(f"zone_id: {zone_id}")
    try:
        models = db.session.query(ShelterBox).filter(ShelterBox.zone_id == zone_id).all()
        return [m.to_dict() for m in models]
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_boxes(common_search):
    try:
        query = build_query(
            table="shelter_boxes",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterBox).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_boxes", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_box(id):
    logger.repository(f"id: {id} remove")
    try:
        query = db.session.query(ShelterBox).filter(ShelterBox.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_box found with id: {id}")
        query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e
