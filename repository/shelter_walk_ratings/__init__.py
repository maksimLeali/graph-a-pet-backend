import uuid
from datetime import datetime

from repository.shelter_walk_ratings.models import ShelterWalkRating
from repository.walk_ratings.models import WalkRatingType
from repository.shelter_walks.models import ShelterWalk
from api.errors import BadRequest
from repository import db
from utils.logger import logger, stringify
from utils.dates import utc_now


def _coerce_type(value):
    if value is None:
        return None
    if isinstance(value, WalkRatingType):
        return value
    try:
        return WalkRatingType[value.upper()]
    except KeyError:
        raise BadRequest(f"Invalid walk rating type: {value}")


def create_shelter_walk_rating(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = utc_now()
        shelter_walk_rating_model = ShelterWalkRating(
            id=str(uuid.uuid4()),
            walk_id=data.get("walk_id"),
            type=_coerce_type(data.get("type")),
            rating=data.get("rating"),
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )
        db.session.add(shelter_walk_rating_model)
        db.session.commit()
        shelter_walk_rating = shelter_walk_rating_model.to_dict()
        logger.check(f"shelter_walk_rating: {stringify(shelter_walk_rating)}")
        return shelter_walk_rating
    except Exception as e:
        logger.error(e)
        raise e


def get_ratings_by_walk(walk_id):
    logger.repository(f"walk_id: {walk_id}")
    try:
        models = db.session.query(ShelterWalkRating).filter(
            ShelterWalkRating.walk_id == walk_id).all()
        return [m.to_dict() for m in models]
    except Exception as e:
        logger.error(e)
        raise e


def get_ratings_by_shelter_pet(shelter_pet_id):
    """All shelter_walk_ratings across every walk of shelter_pet_id, via
    shelter_walk_ratings -> shelter_walks -> shelter_pet_id."""
    logger.repository(f"shelter_pet_id: {shelter_pet_id}")
    try:
        models = (
            db.session.query(ShelterWalkRating)
            .join(ShelterWalk, ShelterWalkRating.walk_id == ShelterWalk.id)
            .filter(ShelterWalk.shelter_pet_id == shelter_pet_id)
            .all()
        )
        return [m.to_dict() for m in models]
    except Exception as e:
        logger.error(e)
        raise e
