import uuid
from datetime import datetime
from sqlalchemy import select, text

from data.ownerships.models import Ownership
from data import db
from data.query_builder import build_where


def create_ownership(data):
    today = datetime.today()
    ownership = Ownership(
        id = f"{uuid.uuid4()}",
        user_id=data["user_id"], 
        pet_id=data["pet_id"], 
        custody_level= data['custody_level'],
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

def get_filtered_ownerships(filters,):
    results = select(Ownership).from_statement(text(
        f"\
            SELECT  * \
            FROM ownerships \
            { '' if len(filters)== 0 else build_where(filters) } \
        "))
    ownerships = db.session.execute(results).scalars()
    return [ownership.to_dict() for ownership in ownerships]

def get_ownership(id):
    return Ownership.query.get(id).to_dict()    