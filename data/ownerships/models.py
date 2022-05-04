from enum import Enum
from data import db
from data.models import *
class CustodyRole(Enum):
    OWNER = "OWNER"
    SUB_OWNER = "SUB_OWNER"
    PET_SITTER = "PET_SITTER"
    

class Ownership(db.Model):
    __tablename__ = 'ownerships'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    pet_id= db.Column(db.String, db.ForeignKey('pets.id'))
    custody_role= db.Column(db.Enum(CustodyRole))
    created_at = db.Column(db.Date)
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "pet_id": self.pet_id,
            "custody_role": self.custody_role.name,
            "created_at": self.created_at
        }