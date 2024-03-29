import uuid
from datetime import datetime
from repository.coats.models import Coat
from repository import db
from api.errors import InternalError, NotFoundError, BadRequest
from utils.logger import logger, stringify

def create_coat(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        coat = Coat(
            id = f"{uuid.uuid4()}",
            length=data["length"], 
            pattern=data["pattern"], 
            colors= data['colors'],
            created_at=today.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        db.session.add(coat)
        db.session.commit()
        return coat.to_dict()
    except Exception as e:
        logger.error(e)
        raise BadRequest(e)
    
def update_coat(id, data):
    logger.repository(
        f"id: {id}\n"\
        f"dta: {stringify(data)}"
    )
    try: 
        coat_model = db.session.query(Coat).filter(Coat.id== id)
        if not coat_model:
            raise NotFoundError(f"no coat found with id: {id}")
        coat_old = coat_model.first().to_dict()
        coat_model.update(data)
        db.session.commit()
        coat= {**coat_old, **coat_model.first().to_dict()}
        logger.check(f'coat: {stringify(coat)}')
        return  coat
    except Exception as e:
        logger.error(e)
        raise e

def get_coats():
    return [coat.to_dict() for coat in Coat.query.all()]

def get_coat(id):
    logger.repository(f"id: {id}")
    try:
        coat_model = Coat.query.get(id)
        if not coat_model:
            raise  
        coat = coat_model.to_dict()
        logger.check(f"coat: {stringify(coat)}")
        return coat
    except Exception as e: 
        logger.error(e)
        raise e