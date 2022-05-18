from typing import Dict
from passlib.hash import pbkdf2_sha256 
import uuid
from datetime import datetime
from data.query_builder import build_query, build_count
from libs.logger import logger
from sqlalchemy import select, text


from data.users.models import User, UserRole
from data import db

def create_user(data):
    today = datetime.today()
    user = User(
        id = f"{uuid.uuid4()}",
        first_name = data["first_name"], 
        last_name = data["last_name"], 
        email=data["email"], 
        role= UserRole.USER.name,
        password= pbkdf2_sha256.hash(data["password"]),
        created_at=today.strftime("%b-%d-%Y")
    )
    db.session.add(user)
    db.session.commit()
    return user.to_dict()
    
def update_user(data, id):

    user = User.query.get(id)
    if user:
        user= {**user, **data}
    db.session.add(user)
    db.session.commit()
    return user 


def get_users(common_search):
    try:
        query = build_query(table="users",search= common_search['search'],search_fields=common_search['search_fields'] ,ordering=common_search["ordering"],filters= common_search['filters'], pagination=common_search['pagination'] )
        manager = select(User).from_statement(text(query))
        users = db.session.execute(manager).scalars()
        return [user.to_dict() for user in users]
    except Exception as e: 
        logger.error(e)
        raise Exception(e)
        
def get_total_items(common_search):
    try:
        query = build_count(table="users",search= common_search['search'],search_fields=common_search['search_fields'] ,filters= common_search['filters'] )
        result = db.session.execute(query)
        return result.first()[0]
    except Exception as e:
        logger.error(e)
        raise Exception(e)
    
def get_user(id):
    return User.query.get(id).to_dict()

async def get_user_from_email(email) -> User:
     return User.query.filter(User.email==email).first().to_dict()
    