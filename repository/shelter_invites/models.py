from enum import Enum
from repository import db, Base
from repository.shelter_roles.models import RoleLevel


class ShelterInviteStatus(Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ShelterInvite(Base):
    __tablename__ = 'shelter_invites'

    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'), nullable=False, index=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, index=True)
    role = db.Column(db.Enum(RoleLevel), nullable=False)
    status = db.Column(db.Enum(ShelterInviteStatus), nullable=False,
                       default=ShelterInviteStatus.PENDING.name)
    invited_by_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        def dt(v):
            return str(v) if v else None
        return {
            "id": self.id,
            "created_at": dt(self.created_at),
            "updated_at": dt(self.updated_at),
            "shelter_id": self.shelter_id,
            "user_id": self.user_id,
            "role": self.role.name if self.role else None,
            "status": self.status.name if self.status else ShelterInviteStatus.PENDING.name,
            "invited_by_id": self.invited_by_id,
        }
