from enum import Enum
from repository import db, Base
class CustodyLevel(Enum):
    OWNER = "OWNER"
    SUB_OWNER = "SUB_OWNER"
    PET_SITTER = "PET_SITTER"
    

class Ownership(Base):
    __tablename__ = 'ownerships'
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    pet_id= db.Column(db.String, db.ForeignKey('pets.id'))
    custody_level= db.Column(db.Enum(CustodyLevel))
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "pet_id": self.pet_id,
            "custody_level": self.custody_level.name,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }