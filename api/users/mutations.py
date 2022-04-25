# mutations.py
from datetime import date
from ariadne import convert_kwargs_to_snake_case
from data import db
from .models import User
import bcrypt
import uuid

@convert_kwargs_to_snake_case
def create_user_resolver(obj, info, data):
    try:
        print(data)
        today = date.today()
        salt = bcrypt.gensalt()
        user = User(
            id = uuid.uuid4(),
            first_name = data["first_name"], 
            last_name = data["last_name"], 
            email=data["email"], 
            salt=salt, 
            password=bcrypt.hashpw(bytes(data["password"], encoding='utf-8'), salt),  
            created_at=today.strftime("%b-%d-%Y")
        )
        print(user)
        db.session.add(user)
        db.session.commit()
        payload = {
            "success": True,
            "user": user.to_dict()
        }
    except ValueError:  # date format errors
        payload = {
            "success": False,
            "errors": [f"Incorrect date format provided. Date should be in "
                       f"the format dd-mm-yyyy"]
        }
    return payload

@convert_kwargs_to_snake_case
def update_user_resolver(obj, info, id, data):
    try:
        user = User.query.get(id)
        if user:
            user= {**user, **data}
        db.session.add(user)
        db.session.commit()
        payload = {
            "success": True,
            "user": user.to_dict()
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload