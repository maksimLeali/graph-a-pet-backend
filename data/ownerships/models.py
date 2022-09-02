from enum import Enum
from data import db
from data.models import *
from datetime import datetime
class CustodyLevel(Enum):
    OWNER = "OWNER"
    SUB_OWNER = "SUB_OWNER"
    PET_SITTER = "PET_SITTER"
    

class Ownership(db.Model):
    __tablename__ = 'ownerships'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    pet_id= db.Column(db.String, db.ForeignKey('pets.id'))
    custody_level= db.Column(db.Enum(CustodyLevel))
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    updated_at = db.Column(db.DateTime)
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "pet_id": self.pet_id,
            "custody_level": self.custody_level.name,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }