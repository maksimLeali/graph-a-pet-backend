import uuid
from datetime import datetime
from data.pet_bodies.models import PetBody
from data import db

def create_pet_body(data):
    today = datetime.today()

    print('////////')
    print('////////')
    print('////////')
    print(data)
    pet_body = PetBody(
        id = f"{uuid.uuid4()}",
        breed=data["breed"], 
        family= data['family'],
        coat_id= data["coat_id"],
        created_at=today.strftime("%b-%d-%Y")
    )
    db.session.add(pet_body)
    db.session.commit()

    print(pet_body.to_dict())
    return pet_body.to_dict()
    
def update_pet_body(data):
    pet_body = PetBody.query.get(id)
    if pet_body:
        pet_body= {**pet_body, **data}
    db.session.add(pet_body)
    db.session.commit()
    return pet_body

def get_pet_bodies():
    return [pet_body.to_dict() for pet_body in PetBody.query.all()]

def get_pet_body(id):
    return PetBody.query.get(id).to_dict() 