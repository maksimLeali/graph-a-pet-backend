import uuid
from datetime import datetime
from repository.pet_bodies.models import PetBody
from repository import db
from api.errors import InternalError, NotFoundError
from utils.logger import logger, stringify

def create_pet_body(data):
    today = datetime.today()
    pet_body = PetBody(
        id = f"{uuid.uuid4()}",
        breed=data["breed"], 
        family= data['family'],
        coat_id= data["coat_id"],
        created_at=today.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    db.session.add(pet_body)
    db.session.commit()
    return pet_body.to_dict()
    
def update_pet_body(id, data):
    logger.repository(
        f"id: {id}\n"\
        f"dta: {stringify(data)}"
    )
    try: 
        pet_body_model = db.session.query(PetBody).filter(PetBody.id== id)
        if not pet_body_model:
            raise NotFoundError(f"no pet_body found with id: {id}")
        pet_body_old = pet_body_model.first().to_dict()
        pet_body_model.update(data)
        db.session.commit()
        pet_body= {**pet_body_old, **pet_body_model.first().to_dict()}
        logger.check(f'pet_body: {stringify(pet_body)}')
        return  pet_body
    except Exception as e:
        logger.error(e)
        raise e

def get_pet_bodies():
    return [pet_body.to_dict() for pet_body in PetBody.query.all()]

def get_pet_body(id):
    logger.repository(f"id: {id}")
    try:
        pet_body_model= PetBody.query.get(id)
        if not pet_body_model: 
            raise NotFoundError(f"No pet_body found with id {id}")
        pet_body= pet_body_model.to_dict()
        logger.check(f"pet_body: {stringify(pet_body)}")
        return pet_body
    except Exception as e:
        logger.error(e)
        raise e