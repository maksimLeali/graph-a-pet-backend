import data.pets as pets_data
import domain.ownerships as ownerships_domain
import domain.coats as coats_domain

def get_ownerships(obj, info):    
    return ownerships_domain.get_filtered_ownerships({"pet_id": obj['id']})


def create_pet(data):
    coat = coats_domain.create_coat(data['coat'])
    print('*********************')
    print('*********************')
    print(coat)
    print('*********************')
    print('*********************')
    data['coat_id'] = coat['id']
    return pets_data.create_pet(data)

def update_pet(id, data):
    return pets_data.update_pet(id, data)

def get_pets():
    return pets_data.get_pets()

def get_pet(id): 
    return pets_data.get_pet(id)