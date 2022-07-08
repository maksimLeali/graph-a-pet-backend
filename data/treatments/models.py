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
    
class Treatment(db.Model):
    __tablename__ = 'treatments',
    name = db.Column(db.STRING)
    date = db.Column(db.DateTime)
    type = db.Column(db.Enum(TreatmentType), default=TreatmentType.REMINDER.name)
    health_card_id= db.Column(db.String, db.ForeignKey('health_cards.id'))
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))