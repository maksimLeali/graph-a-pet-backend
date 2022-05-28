import uuid
from datetime import datetime
from data.coats.models import Coat
from data import db
from api.errors import InternalError, NotFoundError, BadRequest
from libs.logger import logger, stringify

def create_coat(data):
    logger.data(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        coat = Coat(
            id = f"{uuid.uuid4()}",
            length=data["length"], 
            pattern=data["pattern"], 
            colors= data['colors'],
            created_at=today.strftime("%b-%d-%Y")
        )
        db.session.add(coat)
        db.session.commit()
        return coat.to_dict()
    except Exception as e:
        logger.error(e)
        raise BadRequest(e)
    
def update_coat(data):
    coat = Coat.query.get(id)
    if coat:
        coat= {**coat, **data}
    db.session.add(coat)
    db.session.commit()
    return coat

def get_coats():
    return [coat.to_dict() for coat in Coat.query.all()]

def get_coat(id):
    logger.data(f"id: {id}")
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