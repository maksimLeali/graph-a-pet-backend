import uuid
from datetime import datetime

from repository.pet_weights.models import PetWeight
from repository import db
from utils.logger import logger, stringify
from utils.dates import utc_now


def create_pet_weight(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = utc_now()
        model = PetWeight(
            id=str(uuid.uuid4()),
            pet_id=data.get("pet_id"),
            weight_kg=data.get("weight_kg"),
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        )
        db.session.add(model)
        db.session.commit()
        weight = model.to_dict()
        logger.check(f"pet_weight: {stringify(weight)}")
        return weight
    except Exception as e:
        logger.error(e)
        raise e


def get_weights_by_pet(pet_id):
    logger.repository(f"pet_id: {pet_id}")
    try:
        models = (
            db.session.query(PetWeight)
            .filter(PetWeight.pet_id == pet_id)
            .order_by(PetWeight.created_at.asc())
            .all()
        )
        return [m.to_dict() for m in models]
    except Exception as e:
        logger.error(e)
        raise e


def get_latest_weight(pet_id):
    logger.repository(f"pet_id: {pet_id}")
    try:
        model = (
            db.session.query(PetWeight)
            .filter(PetWeight.pet_id == pet_id)
            .order_by(PetWeight.created_at.desc())
            .first()
        )
        return model.to_dict() if model else None
    except Exception as e:
        logger.error(e)
        raise e
