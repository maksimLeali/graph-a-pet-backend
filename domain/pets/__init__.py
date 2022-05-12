import data.pets as pets_data
import domain.ownerships as ownerships_domain
import domain.pet_bodies as pet_bodies_domain

def get_ownerships(obj, info):    
    return ownerships_domain.get_filtered_ownerships({"lists": None, "ranges": None, "fixeds": {"user_id": obj['id']}})

def get_body(obj, info):
    return pet_bodies_domain.get_pet_body(obj['body_id'])

def create_pet(data):
    body = pet_bodies_domain.create_pet_body(data['body'])
    data['body_id'] = body['id']
    return pets_data.create_pet(data)

def update_pet(id, data):
    return pets_data.update_pet(id, data)

def get_pets():
    return pets_data.get_pets()

def get_pet(id): 
    return pets_data.get_pet(id)