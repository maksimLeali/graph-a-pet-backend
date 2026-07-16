from enum import Enum
from repository import db, Base
from utils.dates import iso_z
class CustodyLevel(Enum):
    OWNER = "OWNER"
    SUB_OWNER = "SUB_OWNER"
    PET_SITTER = "PET_SITTER"


class OwnershipStatus(Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Ownership(Base):
    __tablename__ = 'ownerships'
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    pet_id= db.Column(db.String, db.ForeignKey('pets.id'))
    custody_level= db.Column(db.Enum(CustodyLevel))
    # ACCEPTED by default so existing links / self-links are effective at once;
    # invites to other users are created PENDING and flipped on accept/reject.
    status = db.Column(db.Enum(OwnershipStatus), default=OwnershipStatus.ACCEPTED.name)
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "pet_id": self.pet_id,
            "custody_level": self.custody_level.name,
            "status": self.status.name if self.status else OwnershipStatus.ACCEPTED.name,
            "created_at": iso_z(self.created_at),
            "updated_at": iso_z(self.updated_at) if self.updated_at else None,
        }