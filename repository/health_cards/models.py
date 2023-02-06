from enum import Enum
from repository import db, Base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class HealthCard(Base):
    __tablename__ =  'health_cards'
    id =  db.Column(db.String, primary_key=True)
    pet_id=  db.Column(db.String, db.ForeignKey('pets.id'))
    treatments= db.relationship("Treatment", uselist=True, backref='health_cards')
    notes =  db.Column(JSONB)
    created_at =  db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    def to_dict(self) :
        return  {
            "id":  self.id,
            "created_at":  str(self.created_at),
            "pet_id":  self.pet_id,
            "notes":  self.notes,
        }