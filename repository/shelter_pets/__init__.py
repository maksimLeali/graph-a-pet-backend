import uuid
from datetime import datetime
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_pets.models import ShelterPet
from repository.query_builder import build_query, build_count, build_where


def create_shelter_pet(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        shelter_pet = ShelterPet(
            id=f"{uuid.uuid4()}",
            shelter_id=data["shelter_id"],
            pet_id=data["pet_id"],
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        )
        db.session.add(shelter_pet)
        db.session.commit()
        return shelter_pet.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def create_shelter_pets(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        shelter_id = data["shelter_id"]
        shelter_pets = [
            ShelterPet(
                id=f"{uuid.uuid4()}",
                shelter_id=shelter_id,
                pet_id=pet_id,
                created_at=today,
            )
            for pet_id in data["pet_ids"]
        ]
        db.session.add_all(shelter_pets)
        db.session.commit()
        return [sp.to_dict() for sp in shelter_pets]
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_pet(id, data):
    logger.repository(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        shelter_pet_model = db.session.query(ShelterPet).filter(ShelterPet.id == id)
        if not shelter_pet_model.first():
            raise NotFoundError(f"no shelter_pet found with id: {id}")
        shelter_pet_old = shelter_pet_model.first().to_dict()
        shelter_pet_model.update(data)
        db.session.commit()
        shelter_pet = {**shelter_pet_old, **shelter_pet_model.first().to_dict()}
        logger.check(f'shelter_pet: {stringify(shelter_pet)}')
        return shelter_pet
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_pets(common_search):
    try:
        query = build_query(table="shelter_pets", ordering=common_search["ordering"], filters=common_search['filters'], pagination=common_search['pagination'])
        manager = select(ShelterPet).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_filtered_shelter_pets(filters):
    results = select(ShelterPet).from_statement(text(
        f"\
            SELECT  * \
            FROM shelter_pets \
            { '' if len(filters)== 0 else build_where(filters) } \
        "))
    shelter_pets = db.session.execute(results).scalars()
    return [shelter_pet.to_dict() for shelter_pet in shelter_pets]


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_pets", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_pet(id):
    logger.repository(f"id: {id}")
    try:
        shelter_pet_model = ShelterPet.query.get(id)
        if not shelter_pet_model:
            raise NotFoundError(f"no shelter_pet found with id: {id}")
        return shelter_pet_model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_pet(id):
    logger.repository(f"id: {id}  remove")
    try:
        shelter_pet_model = db.session.query(ShelterPet).filter(ShelterPet.id == id)
        if not shelter_pet_model:
            raise NotFoundError(f"no shelter_pet found with id: {id}")
        shelter_pet_model.delete()
        db.session.commit()
        logger.check(f"deleted {id}")
    except Exception as e:
        logger.error(e)
        raise e
