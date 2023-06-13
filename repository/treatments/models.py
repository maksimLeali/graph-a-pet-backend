from enum import Enum
from repository import db, Base
from repository.models import *
from sqlalchemy.dialects.postgresql import JSONB


class TreatmentType(Enum):
    VACCINE = "VACCINE",
    ANTIPARASITIC = "ANTIPARASITIC",
    TABLET = "TABLET",
    OPERATION = "OPERATION",
    REMINDER = "REMINDER",

class treatmentDuration(Enum):
    TEN_MINUTES="TEN_MINUTES",
    QUARTER_HOUR="QUARTER_HOUR",
    THREE_QUARTER="THREE_QUARTER",
    HALF_HOUR="HALF_HOUR",
    HOUR="HOUR",
    HOUR_AND_HALF="HOUR_AND_HALF",
    TWO_HOURS="TWO_HOURS"


class FrequencyUnit(Enum):
    DAILY = "DAILY",
    WEEKLY = "WEEKLY",
    MONTHLY = "MONTHLY",
    YEARLY = "YEARLY"


class Treatment(Base):
    __tablename__ = 'treatments'
    
    name = db.Column(db.String)
    date = db.Column(db.DateTime)
    booster_id = db.Column(db.String)
    type = db.Column(db.Enum(TreatmentType),
                     default=TreatmentType.REMINDER.name)
    health_card_id = db.Column(db.String, db.ForeignKey('health_cards.id'))
    logs = db.Column(db.ARRAY(db.String))
    frequency_value = db.Column(db.Integer)
    frequency_unit = db.Column(db.Enum(FrequencyUnit))
    frequency_times = db.Column(db.Integer)
    duration = db.Column(db.Enum(treatmentDuration),
                     default=treatmentDuration.HALF_HOUR.name) 
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "frequency_value": self.frequency_value,
            "frequency_unit": self.frequency_unit.name if self.frequency_unit else None,
            "frequency_times": self.frequency_times,
            "booster_id": self.booster_id,
            "type": self.type.name,
            "health_card_id": self.health_card_id,
            "updated_at": str(self.updated_at) if self.updated_at else None,
            "logs": self.logs,
            "created_at": self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "duration": self.duration.name if (self.duration ) else treatmentDuration.HALF_HOUR.name
        }
