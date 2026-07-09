from __future__ import annotations
from enum import Enum
from typing import Any
from repository import Base, db


class ShelterType(Enum):
    OFFICIAL_SHELTER = "OFFICIAL_SHELTER"
    PERSONAL_WORKSPACE = "PERSONAL_WORKSPACE"


class ShelterVerificationStatus(Enum):
    UNVERIFIED = "UNVERIFIED"
    PENDING_CLAIM = "PENDING_CLAIM"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ShelterVisibility(Enum):
    PRIVATE = "PRIVATE"
    UNLISTED = "UNLISTED"
    PUBLIC = "PUBLIC"


class Shelter(Base):
    __tablename__ = "shelters"

    shelters_roles = db.relationship("ShelterRole", uselist=True, backref='shelters')
    name = db.Column(db.String, nullable=False)
    street = db.Column(db.String, nullable=False)
    street_number = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    province_code = db.Column(db.String, nullable=False)
    postal_code = db.Column(db.String, nullable=False)
    region = db.Column(db.String, nullable=True)
    district = db.Column(db.String, nullable=True)
    contacts = db.Column(db.JSON, nullable=False, default=list)
    # existing shelters default to OFFICIAL/VERIFIED/PUBLIC so behavior before
    # this feature (all shelters equally "official" and visible) is preserved
    type = db.Column(db.Enum(ShelterType), nullable=False, default=ShelterType.OFFICIAL_SHELTER.name)
    verification_status = db.Column(db.Enum(ShelterVerificationStatus), nullable=False,
                                     default=ShelterVerificationStatus.VERIFIED.name)
    visibility = db.Column(db.Enum(ShelterVisibility), nullable=False,
                           default=ShelterVisibility.PUBLIC.name)
    # public discovery profile (all optional; owner/manager opt in by filling them)
    public_description = db.Column(db.Text, nullable=True)
    public_contact_email = db.Column(db.String, nullable=True)
    public_contact_phone = db.Column(db.String, nullable=True)
    accepts_volunteers = db.Column(db.Boolean, nullable=False, default=False)
    public_location_label = db.Column(db.String, nullable=True)
    public_lat = db.Column(db.Float, nullable=True)
    public_lng = db.Column(db.Float, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "street": self.street,
            "street_number": self.street_number,
            "city": self.city,
            "province_code": self.province_code,
            "postal_code": self.postal_code,
            "region": self.region,
            "district": self.district,
            "contacts": self.contacts or [],
            "type": self.type.name if self.type else ShelterType.OFFICIAL_SHELTER.name,
            "verification_status": self.verification_status.name if self.verification_status else ShelterVerificationStatus.VERIFIED.name,
            "visibility": self.visibility.name if self.visibility else ShelterVisibility.PUBLIC.name,
            "public_description": self.public_description,
            "public_contact_email": self.public_contact_email,
            "public_contact_phone": self.public_contact_phone,
            "accepts_volunteers": bool(self.accepts_volunteers),
            "public_location_label": self.public_location_label,
            "public_lat": self.public_lat,
            "public_lng": self.public_lng,
            "created_at": self.created_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }

    def __repr__(self) -> str:
        return f"<Shelter id={self.id} name={self.name}>"
