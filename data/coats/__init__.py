import uuid
from datetime import datetime
from data.coats.models import Coat
from data import db

def create_coat(data):
    today = datetime.today()
    coat = Coat(
        id = f"{uuid.uuid4()}",
        length=data["length"], 
        pattern=data["pattern"], 
        colors= data['colors'],
        created_at=today.strftime("%b-%d-%Y")
    )
    print('^^^+++')
    print('^^^+++')
    print('^^^+++')
    print('^^^+++')
    print('^^^+++')
    db.session.add(coat)
    db.session.commit()
    return coat.to_dict()
    
def update_coat(data):
    coat = Coat.query.get(id)
    if coat:
        coat= {**coat, **data}
    db.session.add(coat)
    db.session.commit()
    return coat

def get_coats():
    return [coat.to_dict() for coat in Coat.query.all()]

def get_coat(id):
    return Coat.query.get(id).to_dict() 