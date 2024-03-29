from enum import Enum
from repository import db, Base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class HealthCard(Base):
    __tablename__ =  'health_cards'
    pet_id=  db.Column(db.String, db.ForeignKey('pets.id'))
    treatments= db.relationship("Treatment", uselist=True, backref='health_cards')
    notes =  db.Column(db.ARRAY(db.String))
    created_at =  db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    def to_dict(self) :
        return  {
            "id":  self.id,
            "created_at":  str(self.created_at),
            "pet_id":  self.pet_id,
            "notes":  self.notes,
        }