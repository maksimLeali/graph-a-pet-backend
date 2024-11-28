import repository.pet_bodies as pet_bodies_data
import domain.pets as pets_domain

from utils.logger import logger, stringify

def get_pet(obj,info):
    return pets_domain.get_pet(obj['pet_id'])


def create_pet_body(data):
    try: 
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
        pet_body= pet_bodies_data.update_pet_body(id, data)
        logger.check(f"pet_body: {stringify(pet_body)}")
        return pet_body
    except Exception as e:
        logger.error(e)
        raise e        

def get_pet_bodies():
    return pet_bodies_data.get_pet_bodies()

def get_pet_body(id): 
    return pet_bodies_data.get_pet_body(id)
