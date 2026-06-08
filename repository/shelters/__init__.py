import uuid
from datetime import datetime
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy import select, text
from repository.query_builder import build_query, build_count
from utils.logger import logger, stringify
from api.errors import NotFoundError, BadRequest

from repository.shelters.models import Shelter
from repository import db


def create_shelter(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        shelter_model = Shelter(
            id=str(uuid.uuid4()),
            name=data["name"],
            street=data["street"],
            street_number=data["street_number"],
            city=data["city"],
            province_code=data["province_code"],
            postal_code=data["postal_code"],
            region=data.get("region"),
            district=data.get("district"),
            contacts=data.get("contacts") or [],
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        )
        db.session.add(shelter_model)
        db.session.commit()
        shelter = shelter_model.to_dict()
        logger.check(f"shelter: {stringify(shelter)}")
        return shelter
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter(id, data):
    logger.repository(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        shelter_model = db.session.query(Shelter).filter(Shelter.id == id)
        if not shelter_model.first():
            raise NotFoundError(f"no shelter found with id: {id}")
        shelter_old = shelter_model.first().to_dict()
        shelter_model.update(data)
        db.session.commit()
        shelter = {**shelter_old, **shelter_model.first().to_dict()}
        logger.check(f"shelter: {stringify(shelter)}")
        return shelter
    except InvalidRequestError as e:
        logger.error(e)
        raise BadRequest(e)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelters(common_search):
    logger.repository(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="shelters", ordering=common_search["ordering"],
                            filters=common_search['filters'], pagination=common_search['pagination'])
        manager = select(Shelter).from_statement(text(query))
        shelters = db.session.execute(manager).scalars()
        return [shelter.to_dict() for shelter in shelters]
    except Exception as e:
        logger.error(e)
        raise e


def get_all_shelters():
    logger.repository("fetching all shelters")
    try:
        shelters = Shelter.query.all()
        logger.check(f"shelters: {len(shelters)}")
        return shelters
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter(id, soft=True):
    logger.repository(f"id: {id} {'soft' if soft else 'hard'} remove")
    try:
        shelter_model = db.session.query(Shelter).filter(Shelter.id == id)
        if not shelter_model.first():
            raise NotFoundError(f"no shelter found with id: {id}")
        shelter_model.delete()
        db.session.commit()
        logger.check(f"hard deleted {id}")
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelters", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter(id):
    logger.repository(f"id {id}")
    try:
        shelter_model = Shelter.query.filter(Shelter.id == id).first()
        if not shelter_model:
            raise NotFoundError(f"No shelter found with id {id}")
        shelter = shelter_model.to_dict()
        logger.check(f"shelter: {stringify(shelter)}")
        return shelter
    except Exception as e:
        logger.error(e)
        raise e
