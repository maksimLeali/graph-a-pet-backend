import bcrypt
import uuid
from datetime import date

from .models import User, UserRole
from data import db 

def create_user(data):
    today = date.today()
    salt = bcrypt.gensalt()
    user = User(
        id = uuid.uuid4(),
        first_name = data["first_name"], 
        last_name = data["last_name"], 
        email=data["email"], 
        salt=salt, 
        role= UserRole.USER.name,
        password=bcrypt.hashpw(bytes(data["password"], encoding='utf-8'), salt),  
        ownerships_id=[],
        created_at=today.strftime("%b-%d-%Y")
    )
    db.session.add(user)
    db.session.commit()
    return user
    
def update_user(data):

    user = User.query.get(id)
    if user:
        user= {**user, **data}
    db.session.add(user)
    db.session.commit()
    return user 

def get_users():
    return [user.to_dict() for user in User.query.all()]

def get_user(id):
    return User.query.get(id)