import repository.shelter_pets as shelter_pets_data
import domain.pets as pets_domain
import domain.shelters as shelters_domain
from api.errors import NotFoundError
import domain.damnationes_memoriae as damnatio_domain
from utils.logger import logger, stringify
from math import ceil


def get_pet(obj, info):
    return pets_domain.get_pet(obj['pet_id'])


def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj['shelter_id'])


def create_shelter_pet(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter = shelters_domain.get_shelter(data.get('shelter_id'))
        if shelter is None:
            raise NotFoundError(f'no shelter found with id {data.get("shelter_id")}')
        pet = pets_domain.get_pet(data.get('pet_id'))
        if pet is None:
            raise NotFoundError(f'no pet found with id {data.get("pet_id")}')
        return shelter_pets_data.create_shelter_pet(data)
    except Exception as e:
        logger.error(e)
        raise e


def create_shelter_pets(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter_id = data.get('shelter_id')
        shelter = shelters_domain.get_shelter(shelter_id)
        if shelter is None:
            raise NotFoundError(f'no shelter found with id {shelter_id}')
        pet_ids = data.get('pet_ids') or []
        for pet_id in pet_ids:
            pet = pets_domain.get_pet(pet_id)
            if pet is None:
                raise NotFoundError(f'no pet found with id {pet_id}')
        return shelter_pets_data.create_shelter_pets(data)
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter_pet(id, data):
    logger.domain(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        shelter_pet = shelter_pets_data.update_shelter_pet(id, {})
        logger.check(f"shelter_pet: {stringify(shelter_pet)}")
        return shelter_pet
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_pet(id, user_id):
    logger.domain(f"id {id} remove")
    try:
        shelter_pet = shelter_pets_data.get_shelter_pet(id)
        memoriae_id = damnatio_domain.delete_row(id, 'shelter_pets', shelter_pet, user_id)
        return memoriae_id
    except Exception as e:
        logger.error(e)
        raise e


def get_paginated_shelter_pets(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        shelter_pets = get_shelter_pets(common_search)
        return (shelter_pets, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_pets(common_search):
    try:
        return shelter_pets_data.get_shelter_pets(common_search)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_pet(id):
    return shelter_pets_data.get_shelter_pet(id)


def get_filtered_shelter_pets(filters):
    return shelter_pets_data.get_filtered_shelter_pets(filters)


def get_pagination(common_search):
    try:
        total_items = shelter_pets_data.get_total_items(common_search)
        page_size = common_search['pagination']['page_size']
        total_pages = ceil(total_items / page_size)
        current_page = common_search['pagination']['page']
        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error(e)
        raise e
