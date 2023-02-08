import uuid
from datetime import datetime
import pydash as py_
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from .models import Pet, Gender
from repository import db, inspector
from repository.query_builder import build_query, build_count
from utils import camel_to_snake
from utils.logger import logger, stringify
from controller.errors import NotFoundError, BadRequest



def build_where(filters) -> str:
    keys = py_.keys(filters)
    formatted_values = ""
    for i, key in enumerate(keys, start=1):
        formatted_values += (
            f"{camel_to_snake(key)} = '{filters[key]}' {'AND' if i < len(filters) else '' }")
    return f"WHERE { formatted_values }"


def create_pet(data: dict):
    today = datetime.today()

    pet = Pet(
        id=f"{uuid.uuid4()}",
        name=data.get("name"),
        birthday=data.get("birthday") ,
        neutered=data.get("neutered") ,
        body_id=data.get("body_id") ,
        gender=data.get("gender") ,
        disciplines=data.get('disciplines') ,
        temperament=data.get('temperament') ,
        weight_kg=data.get("weight_kg") ,
        chip_code=data.get("chip_code") ,
        diet=data.get('diet'),
        intollerance=data.get("intollerance") ,
        created_at=today.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    db.session.add(pet)
    db.session.commit()

    return pet.to_dict()


def update_pet(id, data):
    logger.repository(
        f"id: {id}\n"\
        f"dta: {stringify(data)}"
    )
    try: 
        pet_model = db.session.query(Pet).filter(Pet.id== id)
        if not pet_model:
            raise NotFoundError(f"no pet found with id: {id}")
        pet_old = pet_model.first().to_dict()
        pet_model.update(data)
        db.session.commit()
        pet= {**pet_old, **pet_model.first().to_dict()}
        logger.check(f'pet: {stringify(pet)}')
        return  pet
    except Exception as e:
        logger.error(e)
        raise e


def get_pets(common_search):
    logger.repository(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="pets",ordering=common_search["ordering"],filters= common_search['filters'], pagination=common_search['pagination'] )
        logger.check(f"query: {query}")
        logger.warning(f"query: {query}")
        manager = select(Pet).from_statement(text(query))
        pets_model = db.session.execute(manager).scalars()
        pets = [pet.to_dict() for pet in pets_model]
        logger.check(f"pets found {len(pets)}")
        return pets
    except ProgrammingError as e:
        logger.error(e)
        exception = BadRequest("The fields provided may contains syntax errors")
        exception.extension['extra'] = str(e)
        raise exception
    except Exception as e: 
        logger.error(e)
        raise e

def get_all_pets ():
    logger.repository("fetching all pets")
    try:
        pets  = Pet.query.all()
        logger.check(f"pets: {len(pets)}")
        return pets
    except Exception as e:
        logger.error(e)
        raise e

def get_total_items(common_search):
    try:
        query = build_count(table="pets",filters= common_search['filters'] )
        result = db.session.execute(query).first()
        return result[0] if result!= None else 0
    except Exception as e:
        logger.error(e)
        raise e
    

def get_filtered_ownerships(filters,):
    results = select(Pet).from_statement(text(
        f"\
            SELECT  * \
            FROM pets \
            { '' if len(filters)== 0 else build_where(filters) } \
        "))
    ownerships = db.session.execute(results).scalars()
    return [ownership.to_dict() for ownership in ownerships]


def get_pet(id):
    logger.repository(f"id: {id}")
    try:
        pet_model = Pet.query.get(id)
        if not pet_model:
            raise NotFoundError(f"no pet found with id: {id}")
        pet= pet_model.to_dict()
        return pet
    except Exception as e:
        logger.error(e)
        raise e

def delete_pet(id, ):
    logger.repository(f"id: {id}  remove")
    try: 
        pet_model = db.session.query(Pet).filter(Pet.id == id)
        if not pet_model:
            raise NotFoundError(f"no pet found with id: {id}")
        pet_model.delete()
        db.session.commit()
        logger.check(f"deleted {id}")
    except Exception as e: 
        logger.error(e)
        raise e
    

        

