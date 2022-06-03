from email.policy import default
from enum import Enum
from data import db
from data.models import *
from datetime import datetime

class Gender(Enum):
    MALE="MALE",
    FEMALE="FEMALE",
    NOT_SAID="NOT_SAID"


class Pet(db.Model):
    __tablename__ = 'pets'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
  
    ownerships = db.relationship("Ownership", uselist=True, backref='pets')
    birthday= db.Column(db.Date)
    neutered= db.Column(db.Boolean, default= False)
    body_id= db.Column(db.String, db.ForeignKey('pet_bodies.id'))
    chip_code=db.Column(db.String)
    gender= db.Column(db.Enum(Gender), default = Gender.NOT_SAID.name)
    weight_kg= db.Column(db.Float)
    temperament= db.Column(db.String)
    diet= db.Column(db.ARRAY(db.String), default=[])
    intollerance= db.Column(db.ARRAY(db.String), default= [])
    disciplines= db.Column(db.ARRAY(db.String), default= [])
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    def to_dict(self):
        return {
            "id": self.id,
          
            "name": self.name,
            "birthday": str(self.birthday),
            "neutered": self.neutered,
            "body_id": self.body_id,
            "gender": self.gender.name,        
            "chip_code": self.chip_code,        
            "weight_kg": self.weight_kg,        
            "temperament": self.temperament,        
            "diet": self.diet,        
            "intollerance": self.intollerance,        
            "disciplines": self.disciplines,        
            "created_at": str(self.created_at)
        }
