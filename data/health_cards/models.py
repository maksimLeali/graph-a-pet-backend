from enum import Enum
from data import db
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime


class HealthCard(db.Model):
    __tablename__ = 'health_cards'
    id = db.Column(db.String, primary_key=True)
    pet_id= db.Column(db.String, db.ForeignKey('pets.id'))
    treatments= db.Column(db.JSON)
    notes = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    def to_dict(self):
        return {
            "id": self.id,
            "created_at": str(self.created_at),
            "pet_id": self.pet_id,
            "treatments": self.treatments,
            "notes": self.notes,
        }