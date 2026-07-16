from enum import Enum
from repository import db, Base
from utils.dates import iso_z

class UserRole(Enum):
     USER = "USER"
     ADMIN = "ADMIN"

class User(Base):
    __tablename__ = 'users'
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    role = db.Column(db.Enum(UserRole))
    ownerships = db.relationship("Ownership", uselist=True, backref='users')    
    last_login = db.Column(db.DateTime)
    last_activity  = db.Column(db.DateTime)
    verified = db.Column(db.Boolean, default=False)
    shelters_roles = db.relationship("ShelterRole", uselist=True, backref='users')
    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "password": self.password,
            "role": self.role.name,
            "verified": bool(self.verified) if self.verified is not None else False,
            "created_at": iso_z(self.created_at),
            "updated_at": iso_z(self.updated_at) if self.updated_at else None,
            "last_activity": iso_z(self.last_activity) if self.last_activity else None
        }
        
