from enum import Enum
from repository import db, Base
from utils.dates import iso_z


class ShelterOwnershipStatus(Enum):
    ACTIVE = "ACTIVE"
    TRANSFER_PENDING = "TRANSFER_PENDING"
    ENDED = "ENDED"
    REVOKED = "REVOKED"


class ShelterOwnershipSource(Enum):
    WORKSPACE_CREATOR = "WORKSPACE_CREATOR"
    CLAIM_APPROVAL = "CLAIM_APPROVAL"
    OWNERSHIP_TRANSFER = "OWNERSHIP_TRANSFER"
    PLATFORM_ASSIGNMENT = "PLATFORM_ASSIGNMENT"
    MIGRATION = "MIGRATION"


class ShelterOwnership(Base):
    """Technical ownership of a shelter.

    Deliberately separate from RBAC: holding SHELTER_ADMIN never implies
    ownership and ownership never implies permissions. Proprietary flows
    (transfer, final deletion, claim) require BOTH the RBAC permission and an
    ACTIVE row here.
    """
    __tablename__ = "shelter_ownerships"
    __table_args__ = (
        db.Index(
            "uq_shelter_ownerships_active_shelter_user",
            "shelter_id", "user_id",
            unique=True,
            postgresql_where=db.text("status = 'ACTIVE'"),
        ),
        Base.__table_args__,
    )
    shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=False, index=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.Enum(ShelterOwnershipStatus), nullable=False,
                       default=ShelterOwnershipStatus.ACTIVE, index=True)
    source = db.Column(db.Enum(ShelterOwnershipSource), nullable=False)
    created_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "shelter_id": self.shelter_id,
            "user_id": self.user_id,
            "status": self.status.name if self.status else None,
            "source": self.source.name if self.source else None,
            "created_by_id": self.created_by_id,
            "ended_at": iso_z(self.ended_at) if self.ended_at else None,
            "created_at": iso_z(self.created_at),
            "updated_at": iso_z(self.updated_at) if self.updated_at else None,
        }
