from enum import Enum
from data import db, Base


class PetFamily(Enum) :
    REPTILE= "REPTILE"
    CANINE= "CANINE"
    FELINE= "FELINE"
    BIRDS= "BIRDS"
    FISH= "FISH"

    






class PetBody(Base):
    __tablename__ = 'pet_bodies'
    id = db.Column(db.String, primary_key=True)
    coat_id= db.Column(db.String, db.ForeignKey('coats.id'))
 #   image: Media!
 #   tags: [Tag]!
    family= db.Column(db.Enum(PetFamily))
    breed= db.Column(db.String)
    pet= db.relationship('Pet', backref="pet_bodies", lazy=True, uselist=False )
    
    def to_dict(self):
        return {
            "id": self.id,
            "breed": self.breed,
            "family": self.family.name,
            "coat_id": self.coat_id,
            "created_at": str(self.created_at)
        }