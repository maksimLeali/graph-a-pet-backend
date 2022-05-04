import uuid
from datetime import date

from .models import Pet
from data import db 

def create_pet(data):
    today = date.today()
  
    pet = Pet(
        id = f"{uuid.uuid4()}",
        name = data["name"],
        race = data["race"],
        created_at=today.strftime("%b-%d-%Y")
    )
    db.session.add(pet)
    db.session.commit()
    return pet.to_dict()
    
def update_pet(data):

    pet = Pet.query.get(id)
    if pet:
        pet= {**pet, **data}
    db.session.add(pet)
    db.session.commit()
    return pet

def get_pets():
    return [pet.to_dict() for pet in Pet.query.all()]

def get_pet(id):
    return Pet.query.get(id).to_dict()