from __future__ import annotations
from typing import Any
from repository import Base, db

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
            "created_at": self.created_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }

    def __repr__(self) -> str:
        return f"<Shelter id={self.id} name={self.name}>"
