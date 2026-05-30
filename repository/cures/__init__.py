from typing import Dict
from passlib.hash import pbkdf2_sha256
import uuid
from sqlalchemy.exc import InvalidRequestError
from datetime import datetime, timedelta
from repository.query_builder import build_query, build_count
from utils.logger import logger, stringify
from api.errors import NotFoundError, BadRequest
from sqlalchemy import and_, not_, select, text

from repository.cures.models import Cure, FrequencyUnit
from repository import db

def create_cure(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()

        frequency_unit = data.get("frequency_unit")
        enum_value = None
        if frequency_unit:
            try:
                if isinstance(frequency_unit, FrequencyUnit):
                    enum_value = frequency_unit
                else:
                    enum_value = FrequencyUnit[frequency_unit.upper()]
            except KeyError:
                raise BadRequest(f"Invalid frequency_unit: {frequency_unit}")

        cure_model = Cure(
            id=str(uuid.uuid4()),
            treatment_id=data.get("treatment_id"),
            frequency_value=data.get("frequency_value"),
            frequency_unit=enum_value,
            frequency_times=data.get("frequency_times"),
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )
        db.session.add(cure_model)
        db.session.commit()
        cure = cure_model.to_dict()
        logger.check(f"cure: {stringify(cure)}")
        return cure
    except Exception as e:
        logger.error(e)
        raise e


def update_cure(id, data):
    logger.repository(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        cure_model = db.session.query(Cure).filter(Cure.id == id)
        if not cure_model:
            raise NotFoundError(f"no cure found with id: {id}")
        cure_old = cure_model.first().to_dict()

        if "frequency_unit" in data:
            freq_unit_raw = data.get("frequency_unit")
            if freq_unit_raw is None:
                data["frequency_unit"] = None
            else:
                try:
                    if isinstance(freq_unit_raw, FrequencyUnit):
                        data["frequency_unit"] = freq_unit_raw
                    else:
                        data["frequency_unit"] = FrequencyUnit[freq_unit_raw.upper()]
                except KeyError:
                    raise BadRequest(f"Invalid frequency_unit: {freq_unit_raw}")

        cure_model.update(data)
        db.session.commit()
        cure = {**cure_old, **cure_model.first().to_dict()}
        logger.check(f'cure: {stringify(cure)}')
        return cure
    except InvalidRequestError as e:
        logger.error(e)
        raise BadRequest(e)
    except Exception as e:
        logger.error(e)
        raise e


def get_cures(common_search):
    logger.repository(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="cures", ordering=common_search["ordering"],
                            filters=common_search['filters'], pagination=common_search['pagination'])
        manager = select(Cure).from_statement(text(query))
        cures = db.session.execute(manager).scalars()
        return [cure.to_dict() for cure in cures]
    except Exception as e:
        logger.error(e)
        raise e

def get_all_cures ():
    logger.repository("fetching all cures")
    try:
        cures  = Cure.query.all()
        logger.check(f"cures: {len(cures)}")
        return cures
    except Exception as e:
        logger.error(e)
        raise e
    

def delete_cure(id, soft=True):
    logger.repository(f"id: {id} {'soft' if soft else 'hard'} remove")
    try: 
        cure_model = db.session.query(Cure).filter(Cure.id == id)
        if not cure_model:
            raise NotFoundError(f"no cure found with id: {id}")
        cure_model.delete()
        db.session.commit()
        logger.check(f"hard deleted {id}")
    except Exception as e: 
        logger.error(e)
        raise e
    

def get_total_items(common_search):
    try:
        query = build_count(table="cures", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result != None else 0
    except Exception as e:
        logger.error(e)
        raise e


def get_cure(id):
    logger.repository(f"id {id}")
    try:
        cure_model = Cure.query.filter( Cure.id == id).first()        
        if not cure_model:
            raise NotFoundError(f"No cure found with id {id}")
        cure = cure_model.to_dict()
        logger.check(f"cure: {stringify(cure)}")
        return cure
    except Exception as e:
        logger.error(e)
        raise e

