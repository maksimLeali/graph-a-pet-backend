from enum import Enum
from repository import db, Base
from repository.shelter_roles.models import RoleLevel


class ShelterOwnershipTransferStatus(Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ShelterOwnershipTransfer(Base):
    __tablename__ = 'shelter_ownership_transfers'

    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'), nullable=False, index=True)
    from_user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, index=True)
    # role the previous owner keeps after the transfer; NULL = removed from the shelter
    new_role_for_previous_owner = db.Column(db.Enum(RoleLevel), nullable=True)
    status = db.Column(db.Enum(ShelterOwnershipTransferStatus), nullable=False,
                       default=ShelterOwnershipTransferStatus.PENDING.name, index=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        def dt(v):
            return v.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if v else None
        return {
            "id": self.id,
            "created_at": dt(self.created_at),
            "updated_at": dt(self.updated_at),
            "shelter_id": self.shelter_id,
            "from_user_id": self.from_user_id,
            "to_user_id": self.to_user_id,
            "new_role_for_previous_owner": self.new_role_for_previous_owner.name if self.new_role_for_previous_owner else None,
            "status": self.status.name if self.status else ShelterOwnershipTransferStatus.PENDING.name,
            "accepted_at": dt(self.accepted_at),
            "rejected_at": dt(self.rejected_at),
            "cancelled_at": dt(self.cancelled_at),
            "expires_at": dt(self.expires_at),
        }
