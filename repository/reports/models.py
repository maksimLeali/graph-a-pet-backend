from enum import Enum
from repository import Base, db
from sqlalchemy.sql.sqltypes import DECIMAL as Decimal

class ReportTypes(Enum):
    MISSING="MISSING",
    FOUND="FOUND"

class Report(Base):
    __tablename__= 'reports'
    latitude = db.Column(Decimal(8,6))
    longitude = db.Column(Decimal(9,6))
    type =db.Column(db.Enum(ReportTypes))
    notes = db.Column(db.ARRAY(db.String), default= [])
    pet_id = db.Column(db.String, db.ForeignKey('pets.id'))
    place= db.Column(db.String)
    responders = db.Column(db.ARRAY(db.JSON), default= [])
    reporter = db.Column(db.JSON, default= [])
    def to_dict(self):
        return {
            "id": self.id,
            "place": self.place,
            "type": self.type.name,
            "reporter": self.reporter,
            "responders": self.responders,
            "pet_id": self.pet_id,
            "notes": self.notes,
            "latitude": float(self.latitude),
            "longitude": float(self.longitude),
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at)
        }
    