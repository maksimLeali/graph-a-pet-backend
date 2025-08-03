from enum import Enum
from repository import db, Base

class Gender(Enum):
    MALE="MALE",
    FEMALE="FEMALE",
    NOT_SAID="NOT_SAID"


class CoatLength(Enum) :
    SHORT= "SHORT"
    MEDIUM= "MEDIUM"
    LENGHT= "LENGHT"
    HAIRLESS= "HAIRLESS"


class Pet(Base):
    __tablename__ = 'pets'
    name = db.Column(db.String)
  
    ownerships = db.relationship("Ownership", uselist=True, backref='pets')
    birthday= db.Column(db.Date)
    neutered= db.Column(db.Boolean, default= False)    
    chip_code=db.Column(db.String)
    gender= db.Column(db.Enum(Gender), default = Gender.NOT_SAID.name)
    weight_kg= db.Column(db.Float)
    temperament= db.Column(db.String)
    diet= db.Column(db.ARRAY(db.String), default=[])
    coat_length = db.Column(db.Enum(CoatLength))
    breed= db.Column(db.String)
    intollerance= db.Column(db.ARRAY(db.String), default= [])
    disciplines= db.Column(db.ARRAY(db.String), default= [])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "birthday": str(self.birthday),
            "neutered": self.neutered,
            "gender": self.gender.name,        
            "chip_code": self.chip_code,        
            "weight_kg": self.weight_kg,        
            "temperament": self.temperament,     
            "breed": self.breed,            
            "coat_length": self.coat_length.name,   
            "diet": self.diet,        
            "intollerance": self.intollerance,        
            "disciplines": self.disciplines,        
            "created_at": str(self.created_at)
        }
