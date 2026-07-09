import uuid
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_people.models import ShelterPerson
from repository.query_builder import build_query, build_count

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def create_shelter_person(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        person = ShelterPerson(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            shelter_id=data["shelter_id"],
            user_id=data.get("user_id"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            email=data.get("email"),
            phone=data.get("phone"),
            status=data.get("status") or "VISITOR",
            source=data.get("source") or "MANUAL",
            notes=data.get("notes"),
            created_by_id=data.get("created_by_id"),
        )
        db.session.add(person)
        db.session.commit()
        return person.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_person(id, data):
    logger.repository(f"id: {id}\ndata: {stringify(data)}")
    try:
        query = db.session.query(ShelterPerson).filter(ShelterPerson.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_person found with id: {id}")
        old = query.first().to_dict()
        query.update(dict(data))
        db.session.commit()
        return {**old, **query.first().to_dict()}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_person(id):
    logger.repository(f"id: {id}")
    model = ShelterPerson.query.get(id)
    if not model:
        raise NotFoundError(f"no shelter_person found with id: {id}")
    return model.to_dict()


def archive_shelter_person(id, user_id):
    logger.repository(f"id: {id} archive by {user_id}")
    try:
        query = db.session.query(ShelterPerson).filter(ShelterPerson.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_person found with id: {id}")
        query.update({
            "status": "ARCHIVED",
            "archived_at": datetime.today(),
            "archived_by_id": user_id,
        })
        db.session.commit()
        return query.first().to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_people(common_search):
    try:
        query = build_query(
            table="shelter_people",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterPerson).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_people", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e
