from passlib.hash import pbkdf2_sha256 
import uuid
from datetime import datetime

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

def get_users():
    return [user.to_dict() for user in User.query.all()]


def get_user(id):
    return User.query.get(id).to_dict()

async def get_user_from_email(email) -> User:
     return User.query.filter(User.email==email).first().to_dict()
    