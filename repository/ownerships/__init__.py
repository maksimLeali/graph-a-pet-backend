import uuid
from datetime import datetime
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text
from controller.errors import InternalError, BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.ownerships.models import Ownership
from repository.query_builder import build_query, build_count, build_where


def create_ownership(data):
    today = datetime.today()
    ownership = Ownership(
        id = f"{uuid.uuid4()}",
        user_id=data["user_id"], 
        pet_id=data["pet_id"], 
        custody_level= data['custody_level'],
        created_at=today.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    db.session.add(ownership)
    db.session.commit()
    return ownership.to_dict()
    
def update_ownership(id,data):
    logger.repository(
        f"id: {id}\n"\
        f"dta: {stringify(data)}"
    )
    try: 
        ownership_model = db.session.query(Ownership).filter(Ownership.id== id)
        if not ownership_model:
            raise NotFoundError(f"no ownership found with id: {id}")
        ownership_old = ownership_model.first().to_dict()
        ownership_model.update(data)
        db.session.commit()
        ownership= {**ownership_old, **ownership_model.first().to_dict()}
        logger.check(f'ownership: {stringify(ownership)}')
        return  ownership
    except Exception as e:
        logger.error(e)
        raise e


def get_ownerships(common_search):
    try:
        query = build_query(table="ownerships",ordering=common_search["ordering"],filters= common_search['filters'], pagination=common_search['pagination'] )
        manager = select(Ownership).from_statement(text(query))
        ownershps = db.session.execute(manager).scalars()
        return [pet.to_dict() for pet in ownershps]
    except Exception as e: 
        logger.error(e)
        raise e

def get_filtered_ownerships(filters,):
    results = select(Ownership).from_statement(text(
        f"\
            SELECT  * \
            FROM ownerships \
            { '' if len(filters)== 0 else build_where(filters) } \
        "))
    ownerships = db.session.execute(results).scalars()
    return [ownership.to_dict() for ownership in ownerships]

def get_total_items(common_search):
    try:
        query = build_count(table="ownerships",filters= common_search['filters'] )
        result = db.session.execute(query).first()
        return result[0] if result!= None else 0
    except ProgrammingError as e: 
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e

def get_ownership(id):
    return Ownership.query.get(id).to_dict()    