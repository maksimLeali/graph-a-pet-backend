import data.ownerships as ownerships_data
import domain.users as users_domain
import domain.pets as pets_domain

def get_pet(obj,info):
    return pets_domain.get_pet(obj['pet_id'])

def get_user(obj, info):
    return users_domain.get_user(obj['user_id'])

def create_ownership(data):
    return ownerships_data.create_ownership(data)

def update_ownership(id, data):
    return ownerships_data.update_ownership(id, data)

def get_ownerships():
    return ownerships_data.get_ownerships()

def get_ownership(id): 
    return ownerships_data.get_ownership(id)

def get_filtered_ownerships(filters):
    return ownerships_data.get_filtered_ownerships(filters)