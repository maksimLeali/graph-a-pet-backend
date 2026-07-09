from enum import Enum
from repository import db, Base
from sqlalchemy.dialects.postgresql import JSONB


class ShelterClaimRequestStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ShelterClaimRequest(Base):
    __tablename__ = 'shelter_claim_requests'

    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'), nullable=False, index=True)
    requester_user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.Enum(ShelterClaimRequestStatus), nullable=False,
                       default=ShelterClaimRequestStatus.PENDING.name, index=True)
    # free-form evidence supplied by the requester (documents, links, ids...)
    proof_data = db.Column(JSONB, nullable=True)
    message = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    decision_note = db.Column(db.Text, nullable=True)

    def to_dict(self):
        def dt(v):
            return v.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if v else None
        return {
            "id": self.id,
            "created_at": dt(self.created_at),
            "updated_at": dt(self.updated_at),
            "shelter_id": self.shelter_id,
            "requester_user_id": self.requester_user_id,
            "status": self.status.name if self.status else ShelterClaimRequestStatus.PENDING.name,
            "proof_data": self.proof_data,
            "message": self.message,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": dt(self.reviewed_at),
            "decision_note": self.decision_note,
        }
