from enum import Enum
from repository import db, Base
from utils.dates import iso_z


class ShelterJoinRequestStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ShelterJoinRequest(Base):
    """A user asking to join a shelter as a volunteer (user -> shelter,
    the mirror image of ShelterInvite which is shelter -> user). An OWNER
    or MANAGER of the shelter reviews it; approval creates the real
    ShelterRole (source JOIN_REQUEST)."""
    __tablename__ = 'shelter_join_requests'

    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'), nullable=False, index=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.Enum(ShelterJoinRequestStatus), nullable=False,
                       default=ShelterJoinRequestStatus.PENDING.name, index=True)
    message = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": iso_z(self.created_at),
            "updated_at": iso_z(self.updated_at),
            "shelter_id": self.shelter_id,
            "user_id": self.user_id,
            "status": self.status.name if self.status else ShelterJoinRequestStatus.PENDING.name,
            "message": self.message,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": iso_z(self.reviewed_at),
        }
