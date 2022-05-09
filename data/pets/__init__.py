import uuid
from datetime import datetime
import pydash as py_
from sqlalchemy import select, text

from .models import Pet, Gender
from data import db
from libs.utils import camel_to_snake


def build_where(filters) -> str:
    keys = py_.keys(filters)
    formatted_values = ""
    for i, key in enumerate(keys, start=1):
        formatted_values += (
            f"{camel_to_snake(key)} = '{filters[key]}' {'AND' if i < len(filters) else '' }")
    return f"WHERE { formatted_values }"


def create_pet(data: dict):
    today = datetime.today()

    pet = Pet(
        id=f"{uuid.uuid4()}",
        name=data.get("name"),
        birthday=data.get("birthday") ,
        neutered=data.get("neutered") ,
        body_id=data.get("body_id") ,
        gender=data.get("gender") ,
        disciplines=data.get('disciplines') ,
        temperament=data.get('temperament') ,
        weight_kg=data.get("weight_kg") ,
        chip_code=data.get("chip_code") ,
        diet=data.get('diet'),
        intollerance=data.get("intollerance") ,
        created_at=today.strftime("%b-%d-%Y")
    )
    db.session.add(pet)
    db.session.commit()

    return pet.to_dict()


def update_pet(data):

    pet = Pet.query.get(id)
    if pet:
        pet = {**pet, **data}
    db.session.add(pet)
    db.session.commit()
    return pet


def get_pets():
    return [pet.to_dict() for pet in Pet.query.all()]


def get_filtered_ownerships(filters,):
    results = select(Pet).from_statement(text(
        f"\
            SELECT  * \
            FROM pets \
            { '' if len(filters)== 0 else build_where(filters) } \
        "))
    ownerships = db.session.execute(results).scalars()
    return [ownership.to_dict() for ownership in ownerships]


def get_pet(id):
    return Pet.query.get(id).to_dict()
