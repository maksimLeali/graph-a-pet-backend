from typing import Dict
from passlib.hash import pbkdf2_sha256
import uuid
from sqlalchemy.exc import InvalidRequestError
from datetime import datetime, timedelta
from repository.query_builder import build_query, build_count
from utils.logger import logger, stringify
from api.errors import InternalError, NotFoundError, BadRequest
from sqlalchemy import and_, not_, select, text

from repository.users.models import User, UserRole
from repository import db


def create_user(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        user_model = User(
            id=f"{uuid.uuid4()}",
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            role=UserRole.USER.name,
            password=pbkdf2_sha256.hash(data["password"]),
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )
        db.session.add(user_model)
        db.session.commit()
        user = user_model.to_dict()
        logger.check(f"user: {stringify(user)}")
        return user
    except Exception as e:
        logger.error(e)
        raise e


def update_user(id, data):
    logger.repository(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        user_model = db.session.query(User).filter(User.id == id)
        if not user_model:
            raise NotFoundError(f"no user found with id: {id}")
        user_old = user_model.first().to_dict()
        user_model.update(data)
        db.session.commit()
        user = {**user_old, **user_model.first().to_dict()}
        logger.check(f'user: {stringify(user)}')
        return user
    except InvalidRequestError as e:
        logger.error(e)
        raise BadRequest(e)
    except Exception as e:
        logger.error(e)
        raise e


def get_users(common_search):
    logger.repository(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="users", ordering=common_search["ordering"],
                            filters=common_search['filters'], pagination=common_search['pagination'])
        manager = select(User).from_statement(text(query))
        users = db.session.execute(manager).scalars()
        return [user.to_dict() for user in users]
    except Exception as e:
        logger.error(e)
        raise e

def get_all_users ():
    logger.repository("fetching all users")
    try:
        users  = User.query.all()
        logger.check(f"users: {len(users)}")
        return users
    except Exception as e:
        logger.error(e)
        raise e
    
def get_all_active_users():
    logger.repository('fetching all active users ')
    try: 
        users = db.session.query(User).filter(
            and_( 
                 (User.last_activity > datetime.now() -timedelta(days=1) )
                ) 
            ).all()
        logger.check(f"active users: {len(users)}")
        return users
    except Exception as e:
        logger.error(e)
        raise e

def get_all_logged_users_within_x_days(days):
    logger.repository('fetching all active users ')
    try: 
        users = User.query.filter(
            and_(
                    (User.last_activity > datetime.now() -timedelta(days=days))
                )
            ).all()
        logger.info(f"users logged from at least {days} days: {len(users)}")
        return users
    except Exception as e:
        logger.error(e)
        raise e


def delete_user(id, soft=True):
    logger.repository(f"id: {id} {'soft' if soft else 'hard'} remove")
    try: 
        user_model = db.session.query(User).filter(User.id == id)
        if not user_model:
            raise NotFoundError(f"no user found with id: {id}")
        user_model.delete()
        db.session.commit()
        logger.check(f"hard deleted {id}")
    except Exception as e: 
        logger.error(e)
        raise e
    

def get_total_items(common_search):
    try:
        query = build_count(table="users", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result != None else 0
    except Exception as e:
        logger.error(e)
        raise e


def get_user(id):
    logger.repository(f"id {id}")
    try:
        user_model = User.query.filter( User.id == id).first()
        if not user_model:
            raise NotFoundError(f"No user found with id {id}")
        user = user_model.to_dict()
        logger.check(f"user: {stringify(user)}")
        return user
    except Exception as e:
        logger.error(e)
        raise e


def get_user_from_email(email) -> User:
    logger.repository(f'email: {email}')
    try:
        user_model = User.query.filter(
            User.email == email).first()
        if(user_model == None):
            raise NotFoundError('user_not_found')
        logger.check(f"user: {user_model}")
        return user_model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e
