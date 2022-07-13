from enum import Enum
from data import db
from data.models import *
from datetime import datetime

class TreatmentType(Enum):
    VACCINE = "VACCINE",
    ANTIPARASITIC="ANTIPARASITIC",
    TABLET="TABLET",
    OPERATION="OPERATION",
    REMINDER="REMINDER",
    
class FrequencyUnit(Enum) :
    MINUTELY= "MINUTELY",
    DAILY= "DAILY",
    WEEKLY= "WEEKLY",
    MONTHLY= "MONTHLY",
    YEARLY= "YEARLY"
    
class Treatment(db.Model):
    __tablename__ = 'treatments'
    id = db.Column(db.String, primary_key=True)
    date = db.Column(db.DateTime)
    booster_id= db.Column(db.String, db.ForeignKey('treatments.id'))
    type = db.Column(db.Enum(TreatmentType), default=TreatmentType.REMINDER.name)
    health_card_id= db.Column(db.String, db.ForeignKey('health_cards.id'))
    logs = db.Column(db.JSON)
    frequency_value = db.Column(db.Integer)
    frequency_unit = db.Column(db.Enum(FrequencyUnit))
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    def to_dict(self):
        return {
            "id": self.id,
            "date" : self.date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "frequency_value": self.frequency_value,
            "frequency_unit": self.frequency_unit,
            "booster_date": self.booster_date.strftime('%Y-%m-%dT%H:%M:%SZ') if self.booster_date else None,
            "type": self.type.name,
            "health_card_id": self.health_card_id,
            "logs" : self.logs,
            "created_at":self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        }