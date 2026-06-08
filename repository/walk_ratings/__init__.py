import uuid
from datetime import datetime
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy import select, text
from repository.query_builder import build_query, build_count
from utils.logger import logger, stringify
from api.errors import NotFoundError, BadRequest

from repository.walk_ratings.models import WalkRating, WalkRatingType
from repository import db


def _coerce_type(value):
    if value is None:
        return None
    if isinstance(value, WalkRatingType):
        return value
    try:
        return WalkRatingType[value.upper()]
    except KeyError:
        raise BadRequest(f"Invalid walk rating type: {value}")


def create_walk_rating(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        walk_rating_model = WalkRating(
            id=str(uuid.uuid4()),
            walk_id=data.get("walk_id"),
            type=_coerce_type(data.get("type")),
            rating=data.get("rating"),
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )
        db.session.add(walk_rating_model)
        db.session.commit()
        walk_rating = walk_rating_model.to_dict()
        logger.check(f"walk_rating: {stringify(walk_rating)}")
        return walk_rating
    except Exception as e:
        logger.error(e)
        raise e


def update_walk_rating(id, data):
    logger.repository(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        walk_rating_model = db.session.query(WalkRating).filter(WalkRating.id == id)
        if not walk_rating_model:
            raise NotFoundError(f"no walk_rating found with id: {id}")
        walk_rating_old = walk_rating_model.first().to_dict()

        if "type" in data:
            data["type"] = _coerce_type(data.get("type"))

        walk_rating_model.update(data)
        db.session.commit()
        walk_rating = {**walk_rating_old, **walk_rating_model.first().to_dict()}
        logger.check(f'walk_rating: {stringify(walk_rating)}')
        return walk_rating
    except InvalidRequestError as e:
        logger.error(e)
        raise BadRequest(e)
    except Exception as e:
        logger.error(e)
        raise e


def get_walk_ratings(common_search):
    logger.repository(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="walk_ratings", ordering=common_search["ordering"],
                            filters=common_search['filters'], pagination=common_search['pagination'])
        manager = select(WalkRating).from_statement(text(query))
        walk_ratings = db.session.execute(manager).scalars()
        return [walk_rating.to_dict() for walk_rating in walk_ratings]
    except Exception as e:
        logger.error(e)
        raise e


def delete_walk_rating(id, soft=True):
    logger.repository(f"id: {id} {'soft' if soft else 'hard'} remove")
    try:
        walk_rating_model = db.session.query(WalkRating).filter(WalkRating.id == id)
        if not walk_rating_model:
            raise NotFoundError(f"no walk_rating found with id: {id}")
        walk_rating_model.delete()
        db.session.commit()
        logger.check(f"hard deleted {id}")
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="walk_ratings", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result != None else 0
    except Exception as e:
        logger.error(e)
        raise e


def get_walk_rating(id):
    logger.repository(f"id {id}")
    try:
        walk_rating_model = WalkRating.query.filter(WalkRating.id == id).first()
        if not walk_rating_model:
            raise NotFoundError(f"No walk_rating found with id {id}")
        walk_rating = walk_rating_model.to_dict()
        logger.check(f"walk_rating: {stringify(walk_rating)}")
        return walk_rating
    except Exception as e:
        logger.error(e)
        raise e
