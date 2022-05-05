import data.coats as coats_data
import domain.pets as pets_domain

def get_pet(obj,info):
    return pets_domain.get_pet(obj['pet_id'])

def create_coat(data):
    
    return coats_data.create_coat(data)

def update_coat(id, data):
    return coats_data.update_coat(id, data)

def get_coats():
    return coats_data.get_coats()

def get_coat(id): 
    return coats_data.get_coat(id)