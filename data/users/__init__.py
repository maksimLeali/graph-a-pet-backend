from typing import Dict
from passlib.hash import pbkdf2_sha256 
import uuid
from sqlalchemy.exc import InvalidRequestError
from datetime import datetime
from data.query_builder import build_query, build_count
from libs.logger import logger,stringify
from api.errors import InternalError, NotFoundError, BadRequest
from sqlalchemy import select, text


from data.users.models import User, UserRole
from data import db

def create_user(data):
    logger.data(f"data: {stringify(data)}")
    try: 
        today = datetime.today()
        user_model = User(
            id = f"{uuid.uuid4()}",
            first_name = data["first_name"], 
            last_name = data["last_name"], 
            email=data["email"], 
            role= UserRole.USER.name,
            password= pbkdf2_sha256.hash(data["password"]),
            created_at=today.strftime("%b-%d-%Y")
        )
        db.session.add(user_model)
        db.session.commit()
        user= user_model.to_dict()
        logger.check(f"user: {stringify(user)}")
        return user
    except Exception as e:
        logger.error(e)
        raise e
    
def update_user(id, data):
    logger.data(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try: 
        user_model = db.session.query(User).filter(User.id== id)
        if not user_model:
            raise NotFoundError(f"no user found with id: {id}")
        user_old = user_model.first().to_dict()
        user_model.update(data)
        db.session.commit()
        user= {**user_old, **user_model.first().to_dict()}
        logger.check(f'user: {stringify(user)}')
        return  user
    except InvalidRequestError as e:
        logger.error(e) 
        raise BadRequest(e)
    except Exception as e:
        logger.error(e)
        raise e

def get_users(common_search):
    try:
        query = build_query(table="users",search= common_search['search'],search_fields=common_search['search_fields'] ,ordering=common_search["ordering"],filters= common_search['filters'], pagination=common_search['pagination'] )
        manager = select(User).from_statement(text(query))
        users = db.session.execute(manager).scalars()
        return [user.to_dict() for user in users]
    except Exception as e: 
        logger.error(e)
        raise e
        
def get_total_items(common_search):
    try:
        query = build_count(table="users",search= common_search['search'],search_fields=common_search['search_fields'] ,filters= common_search['filters'] )
        result = db.session.execute(query)
        return result.first()[0]
    except Exception as e:
        logger.error(e)
        raise e
    
def get_user(id):
    logger.data(f"id {id}")
    try: 
        user_model= User.query.get(id)
        if not user_model:  
            raise NotFoundError(f"No user found with id {id}") 
        user= user_model.to_dict()
        logger.check(f"user: {stringify(user)}")
        return user
    except Exception as e:
        logger.error(e)
        raise e
    
def get_user_from_email(email) -> User:
     return User.query.filter(User.email==email).first().to_dict()
    