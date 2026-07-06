import uuid
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_areas.models import ShelterArea
from repository.query_builder import build_query, build_count


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def create_shelter_area(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        area = ShelterArea(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            map_id=data["map_id"],
            name=data.get("name"),
            area_type=data.get("area_type"),
            x=data.get("x"),
            y=data.get("y"),
            width=data.get("width"),
            height=data.get("height"),
            color=data.get("color"),
        )
        db.session.add(area)
        db.session.commit()
        return area.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_area(id, data):
    logger.repository(f"id: {id}\ndata: {stringify(data)}")
    try:
        query = db.session.query(ShelterArea).filter(ShelterArea.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_area found with id: {id}")
        old = query.first().to_dict()
        query.update(dict(data))
        db.session.commit()
        return {**old, **query.first().to_dict()}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_area(id):
    logger.repository(f"id: {id}")
    try:
        model = ShelterArea.query.get(id)
        if not model:
            raise NotFoundError(f"no shelter_area found with id: {id}")
        return model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def get_areas_by_map(map_id):
    models = db.session.query(ShelterArea).filter(ShelterArea.map_id == map_id).all()
    return [m.to_dict() for m in models]


def get_shelter_areas(common_search):
    try:
        query = build_query(
            table="shelter_areas",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterArea).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_areas", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_area(id):
    logger.repository(f"id: {id} remove")
    try:
        query = db.session.query(ShelterArea).filter(ShelterArea.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_area found with id: {id}")
        query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e
