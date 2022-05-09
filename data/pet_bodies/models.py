from enum import Enum
from data import db
from data.models import *
from datetime import datetime


class PetFamily(Enum) :
    CANINE="CANINE"
    FELINE="FELINE",
    SERPENTES="SERPENTES"
    BIRDS="BIRDS"
    ARACNIDE="ARACNIDE"
    INSECT="INSECT"
    LIZARD="LIZARD"

    


class PetBody(db.Model):
    __tablename__ = 'pet_bodies'
    id = db.Column(db.String, primary_key=True)
    coat_id= db.Column(db.String, db.ForeignKey('coats.id'))
 #   image: Media!
 #   tags: [Tag]!
    family= db.Column(db.Enum(PetFamily))
    breed= db.Column(db.String)
    pet= db.relationship('Pet', backref="pet_bodies", lazy=True, uselist=False )
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    
    def to_dict(self):
        return {
            "id": self.id,
            "breed": self.breed,
            "family": self.family.name,
            "coat_id": self.coat_id,
            "created_at": str(self.created_at)
        }