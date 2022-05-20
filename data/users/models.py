from enum import Enum
from data import db
from data.models import *
from datetime import datetime

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
    role = db.Column(db.Enum(UserRole))
    ownerships = db.relationship("Ownership", uselist=True, backref='users')
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "password": self.password,
            "role": self.role.name,
            "created_at": str(self.created_at),
        }
        
