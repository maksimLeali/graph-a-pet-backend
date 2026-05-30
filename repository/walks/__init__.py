from typing import Dict
from passlib.hash import pbkdf2_sha256
import uuid
from sqlalchemy.exc import InvalidRequestError
from datetime import datetime, timedelta
from repository.query_builder import build_query, build_count
from utils.logger import logger, stringify
from api.errors import InternalError, NotFoundError, BadRequest
from sqlalchemy import and_, not_, select, text

from repository.walks.models import Walk
from repository import db

def create_walk(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        walk_model = Walk(
            id=str(uuid.uuid4()),
            distance_km=data["distance_km"],
            treatment_id=data.get("treatment_id"),
            overall_rating=data.get("overall_rating"),
            leash_pulling_rating=data.get("leash_pulling_rating"),
            behavior_rating=data.get("behavior_rating"),
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )
        db.session.add(walk_model)
        db.session.commit()
        walk = walk_model.to_dict()
        logger.check(f"walk: {stringify(walk)}")
        return walk
    except Exception as e:
        logger.error(e)
        raise e


def update_walk(id, data):
    logger.repository(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        walk_model = db.session.query(Walk).filter(Walk.id == id)
        if not walk_model:
            raise NotFoundError(f"no walk found with id: {id}")
        walk_old = walk_model.first().to_dict()
        walk_model.update(data)
        db.session.commit()
        walk = {**walk_old, **walk_model.first().to_dict()}
        logger.check(f'walk: {stringify(walk)}')
        return walk
    except InvalidRequestError as e:
        logger.error(e)
        raise BadRequest(e)
    except Exception as e:
        logger.error(e)
        raise e


def get_walks(common_search):
    logger.repository(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="walks", ordering=common_search["ordering"],
                            filters=common_search['filters'], pagination=common_search['pagination'])
        manager = select(Walk).from_statement(text(query))
        walks = db.session.execute(manager).scalars()
        return [walk.to_dict() for walk in walks]
    except Exception as e:
        logger.error(e)
        raise e

def get_all_walks ():
    logger.repository("fetching all walks")
    try:
        walks  = Walk.query.all()
        logger.check(f"walks: {len(walks)}")
        return walks
    except Exception as e:
        logger.error(e)
        raise e
    

def delete_walk(id, soft=True):
    logger.repository(f"id: {id} {'soft' if soft else 'hard'} remove")
    try: 
        walk_model = db.session.query(Walk).filter(Walk.id == id)
        if not walk_model:
            raise NotFoundError(f"no walk found with id: {id}")
        walk_model.delete()
        db.session.commit()
        logger.check(f"hard deleted {id}")
    except Exception as e: 
        logger.error(e)
        raise e
    

def get_total_items(common_search):
    try:
        query = build_count(table="walks", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result != None else 0
    except Exception as e:
        logger.error(e)
        raise e


def get_walk(id):
    logger.repository(f"id {id}")
    try:
        walk_model = Walk.query.filter( Walk.id == id).first()        
        if not walk_model:
            raise NotFoundError(f"No walk found with id {id}")
        walk = walk_model.to_dict()
        logger.check(f"walk: {stringify(walk)}")
        return walk
    except Exception as e:
        logger.error(e)
        raise e

