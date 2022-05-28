import uuid
from datetime import datetime
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text
from api.errors import InternalError, BadRequest
from data.ownerships.models import Ownership
from data import db
from libs.logger import logger
from data.query_builder import build_query, build_count, build_where


def create_ownership(data):
    today = datetime.today()
    ownership = Ownership(
        id = f"{uuid.uuid4()}",
        user_id=data["user_id"], 
        pet_id=data["pet_id"], 
        custody_level= data['custody_level'],
        created_at=today.strftime("%b-%d-%Y")
    )
    db.session.add(ownership)
    db.session.commit()
    return ownership.to_dict()
    
def update_ownership(data):
    ownership = Ownership.query.get(id)
    if ownership:
        ownership= {**ownership, **data}
    db.session.add(ownership)
    db.session.commit()
    return ownership 

def get_ownerships(common_search):
    try:
        query = build_query(table="ownerships",search= common_search['search'],search_fields=common_search['search_fields'] ,ordering=common_search["ordering"],filters= common_search['filters'], pagination=common_search['pagination'] )
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
        query = build_count(table="ownerships",search= common_search['search'],search_fields=common_search['search_fields'] ,filters= common_search['filters'] )
        result = db.session.execute(query)
        return result.first()[0]
    except ProgrammingError as e: 
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e

def get_ownership(id):
    return Ownership.query.get(id).to_dict()    