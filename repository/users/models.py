from enum import Enum
from repository import db, Base

class UserRole(Enum):
     USER = "USER"
     ADMIN = "ADMIN"

class User(Base):
    __tablename__ = 'users'
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    role = db.Column(db.Enum(UserRole))
    ownerships = db.relationship("Ownership", uselist=True, backref='users')
    last_login = db.Column(db.DateTime)
    last_activity  = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "password": self.password,
            "role": self.role.name,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
            "last_activity": str(self.last_activity) if self.last_activity else None
        }
        
