import uuid
from datetime import date

from data.ownerships.models import Ownership
from data import db

def create_ownership(data):
    today = date.today()
    ownership = Ownership(
        id = f"{uuid.uuid4()}",
        user_id=data["user_id"], 
        pet_id=data["pet_id"], 
        custody_role= data['custody_role'],
        created_at=today.strftime("%b-%d-%Y")
    )
    db.session.add(ownership)
    db.session.commit()
    return ownership.to_dict()
    
def update_ownership(data):
    ownership = Ownership.query.get(id)
    if ownership:
        ownership= {**ownership, **data}
    db.session.add(ownership)
    db.session.commit()
    return ownership 

def get_ownerships():
    return [ownership.to_dict() for ownership in Ownership.query.all()]


def get_ownership(id):
    return Ownership.query.get(id).to_dict()

    