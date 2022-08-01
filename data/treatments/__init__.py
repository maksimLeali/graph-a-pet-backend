import uuid
from datetime import datetime
import pydash as py_
from sqlalchemy import select, text, delete
from sqlalchemy.exc import ProgrammingError
from .models import Treatment, Gender
from data import db
from data.query_builder import build_query, build_count
from libs.utils import camel_to_snake
from libs.logger import logger, stringify
from api.errors import NotFoundError, BadRequest


def build_where(filters) -> str:
    keys = py_.keys(filters)
    formatted_values = ""
    for i, key in enumerate(keys, start=1):
        formatted_values += (
            f"{camel_to_snake(key)} = '{filters[key]}' {'AND' if i < len(filters) else '' }")
    return f"WHERE { formatted_values }"

def create_treatment(data: dict):
    logger.data(f"treatment : {stringify(data)}")
    try: 
        today = datetime.today()

        treatment = Treatment(
            id=f"{uuid.uuid4()}",
            date = datetime.strptime(data.get("date"), "%Y-%m-%dT%H:%M:%SZ"),
            booster_id = data.get('booster_id'),
            health_card_id = data.get("health_card_id"),
            type = data.get("type"),
            name = data.get("name"),
            logs = data.get("logs"),
            frequency_unit = data.get("frequency_unit"),
            frequency_value = data.get("frequency_value"),
            created_at=today.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        db.session.add(treatment)
        db.session.commit()

        return treatment.to_dict()
    except Exception as e:
        logger.error(e)
        raise e

def update_treatment(id, data):
    logger.data(
        f"id: {id}\n"\
        f"dta: {stringify(data)}"
    )
    try: 
        treatment_model = db.session.query(Treatment).filter(Treatment.id== id)
        if not treatment_model:
            raise NotFoundError(f"no treatment found with id: {id}")
        treatment_old = treatment_model.first().to_dict()
        treatment_model.update(data)
        db.session.commit()
        treatment= {**treatment_old, **treatment_model.first().to_dict()}
        logger.check(f'treatment: {stringify(treatment)}')
        return  treatment
    except Exception as e:
        logger.error(e)
        raise e
    
    
def delete_treatment(id): 
    logger.data(f"id: {id}")
    try: 
        logger.check(f'deleting: {id}')
        Treatment.query.filter_by(id = id).delete()
        db.session.commit()
        logger.check(f'deleted {id}')
    except Exception as e:
        logger.error(e)
        raise e

def get_treatments(common_search):
    logger.data(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="treatments",ordering=common_search["ordering"],filters= common_search['filters'], pagination=common_search['pagination'] )
        logger.check(f"query: {query}")
        manager = select(Treatment).from_statement(text(query))
        treatments_model = db.session.execute(manager).scalars()
        treatments = [treatment.to_dict() for treatment in treatments_model]
        logger.check(f"treatments found {len(treatments)}")
        return treatments
    except ProgrammingError as e:
        logger.error(e)
        exception = BadRequest("The fields provided may contains syntax errors")
        exception.extension['extra'] = str(e)
        raise exception
    except Exception as e: 
        logger.error(e)
        raise e
    
def get_total_items(common_search):
    try:
        query = build_count(table="treatments",filters= common_search['filters'] )
        result = db.session.execute(query).first()
        return result[0] if result!= None else 0
    except Exception as e:
        logger.error(e)
        raise e
    

def get_filtered_ownerships(filters,):
    results = select(Treatment).from_statement(text(
        f"\
            SELECT  * \
            FROM treatments \
            { '' if len(filters)== 0 else build_where(filters) } \
        "))
    ownerships = db.session.execute(results).scalars()
    return [ownership.to_dict() for ownership in ownerships]


def get_treatment(id):
    logger.data(f"id: {id}")
    try:
        treatment_model = Treatment.query.get(id)
        if not treatment_model:
            raise NotFoundError(f"no treatment found with id: {id}")
        treatment= treatment_model.to_dict()
        return treatment
    except Exception as e:
        logger.error(e)
        raise e
