
import data.coats as coats_data
import domain.pet_bodies as pet_bodies_domain
from libs.logger import logger, stringify

def get_body(obj,info):
    return pet_bodies_domain.get_pet_body(obj['pet_body_id'])

def create_coat(data):
    try:
        return coats_data.create_coat(data)
    except Exception as e:
        logger.error(e)
        raise e

def update_coat(id, data):
    logger.domain(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try: 
        coat= coats_data.update_coat(id, data)
        logger.check(f"coat: {stringify(coat)}")
        return coat
    except Exception as e: 
        logger.error(e)
        raise e

def get_coats():
    return coats_data.get_coats()

def get_coat(id): 
    return coats_data.get_coat(id)