import data.coats as coats_data
import domain.pet_bodies as pet_bodies_domain
from libs.logger import logger

def get_body(obj,info):
    return pet_bodies_domain.get_pet_body(obj['pet_body_id'])

def create_coat(data):
    return coats_data.create_coat(data)

def update_coat(id, data):
    return coats_data.update_coat(id, data)

def get_coats():
    return coats_data.get_coats()

def get_coat(id): 
    return coats_data.get_coat(id)