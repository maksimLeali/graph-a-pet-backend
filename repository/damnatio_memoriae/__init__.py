import uuid
from datetime import datetime
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text

from repository import db
from utils.logger import logger, stringify
from repository.damnatio_memoriae.models import DamnatioMemoriae


def create_damnatio_memoriae(data):
    logger.repository(f'putting {stringify(data)} into the damnatio memoriae')
    try : 
        today = datetime.today()
        damnatio_memoriae = DamnatioMemoriae(
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
        return DamnatioMemoriae.query.get(id).to_dict()    
    except Exception as e: 
        logger.error(e)
        raise e