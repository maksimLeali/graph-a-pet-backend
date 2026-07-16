import uuid
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_map_elements.models import ShelterMapElement
from repository.query_builder import build_query, build_count
from utils.dates import utc_now


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def create_shelter_map_element(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = utc_now()
        element = ShelterMapElement(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            map_id=data["map_id"],
            element_type=data["element_type"],
            x=data.get("x"),
            y=data.get("y"),
            width=data.get("width"),
            height=data.get("height"),
            rotation=data.get("rotation") if data.get("rotation") is not None else 0,
            color=data.get("color"),
            label=data.get("label"),
        )
        db.session.add(element)
        db.session.commit()
        return element.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_map_element(id, data):
    logger.repository(f"id: {id}\ndata: {stringify(data)}")
    try:
        query = db.session.query(ShelterMapElement).filter(ShelterMapElement.id == id)
        if not query.first():
            raise NotFoundError(f"no map element found with id: {id}")
        old = query.first().to_dict()
        query.update(dict(data))
        db.session.commit()
        return {**old, **query.first().to_dict()}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_map_element(id):
    logger.repository(f"id: {id}")
    try:
        model = ShelterMapElement.query.get(id)
        if not model:
            raise NotFoundError(f"no map element found with id: {id}")
        return model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def get_elements_by_map(map_id):
    models = db.session.query(ShelterMapElement).filter(ShelterMapElement.map_id == map_id).all()
    return [m.to_dict() for m in models]


def get_shelter_map_elements(common_search):
    try:
        query = build_query(
            table="shelter_map_elements",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterMapElement).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_map_elements", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_map_element(id):
    logger.repository(f"id: {id} remove")
    try:
        query = db.session.query(ShelterMapElement).filter(ShelterMapElement.id == id)
        if not query.first():
            raise NotFoundError(f"no map element found with id: {id}")
        query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e
