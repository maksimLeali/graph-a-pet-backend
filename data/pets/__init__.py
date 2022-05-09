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


def create_pet(data):
    today = datetime.today()
    print('?????????????')
    print('?????????????')
    print('?????????????')
    print('?????????????')
    print('?????????????')
    print('?????????????')
    print(data)

    try :
        pet = Pet(
            id=f"{uuid.uuid4()}",
            name=data["name"] if data["name"] else None,
            birthday=data["birthday"] if data["birthday"] else None,
            neutered=data["neutered"] if data["neutered"] else False,
            body_id=data["body_id"] if data["body_id"] else None,
            gender=data["gender"] if data["gender"] else Gender.MALE.name,
            disciplines=data['disciplines'] if data['disciplines'] else [],
            temperament=data['temperament'] if data['temperament'] else "",
            weight_kg=data["weight_kg"] if data["weight_kg"] else 0,
            chip_code=data["chip_code"] if data["chip_code"] else "",
            diet=data['diet'] if data['diet'] else [],
            intollerance=data["intollerance"] if data["intollerance"] else [] ,
            created_at=today.strftime("%b-%d-%Y")
        )
        print('***+ùùù§§§§§§§§§§§§§§§')
        db.session.add(pet)
        db.session.commit()
    except Exception as e: 
        print(e)
    print('§§§§§§§§§§§§§§§§§§§')
    print('§§§§§§§§§§§§§§§§§§§')
    print(pet)
    print('§§§§§§§§§§§§§§§§§§§')
    print('§§§§§§§§§§§§§§§§§§§')
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
