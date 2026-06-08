from enum import Enum
from repository import db, Base

class RoleLevel(Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    VOLUNTEER = "VOLUNTEER"
    

class ShelterRole(Base):
    __tablename__ = 'shelter_roles'
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'))
    role = db.Column(db.Enum(RoleLevel))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "shelter_id": self.shelter_id,
            "role": self.role.name if self.role else None,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }