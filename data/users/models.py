from enum import Enum
from data import db
from data.models import *

class UserRole(Enum):
     USER = "USER"
     ADMIN = "ADMIN"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    created_at = db.Column(db.Date)
    role = db.Column(db.Enum(UserRole))
    ownerships = db.relationship("Ownership", uselist=True, backref='users')
    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "password": self.password,
            "role": self.role.name,
            "created_at": str(self.created_at.strftime('%d-%m-%Y')),
        }
        
