import repository.pet_bodies as pet_bodies_data
import domain.pets as pets_domain
import domain.coats as coats_domain
from utils.logger import logger, stringify
import pydash as py_

def get_pet(obj,info):
    return pets_domain.get_pet(obj['pet_id'])

def get_coat(obj, info):
    return coats_domain.get_coat(obj['coat_id'])

def create_pet_body(data):
    try: 
        coat = coats_domain.create_coat(data['coat'])
        data['coat_id'] = coat['id']
        return pet_bodies_data.create_pet_body(data)
    except Exception as e: 
        logger.error(e)
        raise e

def update_pet_body(id, data):
    logger.domain(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try:
        pet_body = pet_bodies_data.get_pet_body(id)
        if(data['coat']!= None):
            coats_domain.update_coat(pet_body['coat_id'], py_.omit(data['coat'], 'id'))
        pet_body= pet_bodies_data.update_pet_body(id, py_.omit(data, 'coat'))
        logger.check(f"pet_body: {stringify(pet_body)}")
        return pet_body
    except Exception as e:
        logger.error(e)
        raise e        

def get_pet_bodies():
    return pet_bodies_data.get_pet_bodies()

def get_pet_body(id): 
    return pet_bodies_data.get_pet_body(id)
