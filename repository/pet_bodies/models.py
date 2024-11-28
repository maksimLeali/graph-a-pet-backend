from enum import Enum
from repository import db, Base


class PetFamily(Enum) :
    REPTILE= "REPTILE"
    CANINE= "CANINE"
    FELINE= "FELINE"
    BIRDS= "BIRDS"
    FISH= "FISH"

class CoatLength(Enum) :
    SHORT= "SHORT"
    MEDIUM= "MEDIUM"
    LENGHT= "LENGHT"
    HAIRLESS= "HAIRLESS"


class PetBody(Base):
    __tablename__ = 'pet_bodies'
    coat_length = db.Column(db.Enum(CoatLength))
    family= db.Column(db.Enum(PetFamily))
    breed= db.Column(db.String)
    pet= db.relationship('Pet', backref="pet_bodies", lazy=True, uselist=False )
    
    def to_dict(self):
        return {
            "id": self.id,
            "breed": self.breed,
            "family": self.family.name,
            "coat_length": self.coat_length,
            "created_at": str(self.created_at)
        }