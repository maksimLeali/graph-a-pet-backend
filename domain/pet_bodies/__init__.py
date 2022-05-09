import data.pet_bodies as pet_bodies_data
import domain.pets as pets_domain
import domain.coats as coats_domain

def get_pet(obj,info):
    return pets_domain.get_pet(obj['pet_id'])

def get_coat(obj, info):
    return coats_domain.get_coat(obj['coat_id'])

def create_pet_body(data):
    print('+++++++++++++++++**+++')
    print('+++++++++++++++++**+++')
    print('+++++++++++++++++**+++')
    coat = coats_domain.create_coat(data['coat'])
    print('coat_created')
    print(coat)
    print('+++++++++++++++++**+++')
    print('+++++++++++++++++**+++')
    data['coat_id'] = coat['id']
    return pet_bodies_data.create_pet_body(data)

def update_pet_body(id, data):
    return pet_bodies_data.update_pet_body(id, data)

def get_pet_bodies():
    return pet_bodies_data.get_pet_bodies()

def get_pet_body(id): 
    return pet_bodies_data.get_pet_body(id)