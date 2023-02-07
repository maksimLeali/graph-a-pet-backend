import uuid
from datetime import datetime
import psycopg2
import sqlalchemy
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text, Table, MetaData

from repository import db
from utils.logger import logger, stringify
from repository.damnationes_memoriae.models import DamnationesMemoriae
from controller.errors import BadRequest, NotFoundError
from repository.query_builder import build_count,  build_query, build_restore


def create_damnatio_memoriae(data):
    logger.repository(f'putting {stringify(data)} into the damnatio memoriae')
    try : 
        today = datetime.today()
        damnatio_memoriae = DamnationesMemoriae(
            id = f"{uuid.uuid4()}",
            original_data=data["original_data"], 
            original_table=data["original_table"], 
            created_at=today.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        db.session.add(damnatio_memoriae)
        db.session.commit()
        return damnatio_memoriae.to_dict()['id']
    except Exception as e:
        logger.error(e)
        raise e

def get_damnatio_memoriae(id):
    logger.repository(f"fetching {id}")
    try :
        memoriae_model= DamnationesMemoriae.query.get(id) 
        if not memoriae_model:
                raise NotFoundError(f"no memory found with id: {id}")
        memoriae= memoriae_model.to_dict()
        logger.check(memoriae)
        return memoriae
    except Exception as e: 
        logger.error(e)
        raise e

def get_damnationes_memoriae(common_search):
    logger.repository(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="damnationes_memoriae",ordering=common_search["ordering"],filters= common_search['filters'], pagination=common_search['pagination'] )
        logger.check(f"query: {query}")
        manager = select(DamnationesMemoriae).from_statement(text(query))
        damnationes_memoriae_model = db.session.execute(manager).scalars()
        damnationes_memoriae = [health_card.to_dict() for health_card in damnationes_memoriae_model]
        logger.check(f"damnationes_memoriae found {len(damnationes_memoriae)}\n{stringify(damnationes_memoriae)}")
        return damnationes_memoriae
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
        query = build_count(table="damnationes_memoriae",filters= common_search['filters'] )
        result = db.session.execute(query).first()
        return result[0] if result!= None else 0
    except ProgrammingError as e: 
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e
    
def restore_memoriae(id):
    try:
        memoriae = get_damnatio_memoriae(id)
        logger.check(f"found {stringify(memoriae)}")
        query = build_restore(memoriae['original_table'], memoriae['original_data'])
        db.session.execute(query)
        db.session.commit()
        delete_memoriae(id)
        return memoriae['original_data'], memoriae['original_table']
    except sqlalchemy.exc.IntegrityError as e:
        if 'psycopg2.errors.UniqueViolation' in str(e):
            message = f'could not resotre {memoriae["original_data"]["id"]} to {memoriae["original_table"]} becouse it already exist'
        else : 
            message= str(e.orig)
        logger.error(message)
        raise BadRequest(message)
    except Exception as e:
        logger.error(e)
        raise e
    
def delete_memoriae(id):
    logger.repository(f"id: {id}  remove")
    try: 
        memoriae_model = db.session.query(DamnationesMemoriae).filter(DamnationesMemoriae.id == id)
        if not memoriae_model:
            raise NotFoundError(f"no memory found with id: {id}")
        memoriae_model.delete()
        db.session.commit()
        logger.check(f"deleted {id}")
    except Exception as e: 
        logger.error(e)
        raise e