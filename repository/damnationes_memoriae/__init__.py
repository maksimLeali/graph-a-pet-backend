import uuid
from datetime import datetime
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text, Table, MetaData

from repository import db
from utils.logger import logger, stringify
from repository.damnationes_memoriae.models import DamnationesMemoriae
from controller.errors import BadRequest
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
        return damnatio_memoriae.to_dict()
    except Exception as e:
        logger.error(e)
        raise e

def get_damnatio_memoriae(id):
    logger.repository(f"fetching {id}")
    try :
        return DamnationesMemoriae.query.get(id).to_dict()    
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
        return memoriae['original_data']
    except Exception as e:
        logger.error(e)
        raise e