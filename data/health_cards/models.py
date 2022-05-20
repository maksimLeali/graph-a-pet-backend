from enum import Enum
from data import db
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime


class HealthCard(db.Model):
    __tablename__ = 'health_cards'
    id = db.Column(db.String, primary_key=True)
    
    treatments= db.Column(db.ARRAY(JSON))
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    def to_dict(self):
        return {
            "id": self.id,
            "created_at": str(self.created_at)
        }