import repository.shelter_pets as shelter_pets_data
import repository.shelter_roles as shelter_roles_data
import domain.pets as pets_domain
import domain.shelters as shelters_domain
from api.errors import NotFoundError, BadRequest
import domain.damnationes_memoriae as damnatio_domain
from utils.logger import logger, stringify
from math import ceil


def get_pet(obj, info):
    return pets_domain.get_pet(obj['pet_id'])


def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj['shelter_id'])


def get_assigned_members(obj, info):
    import domain.users as users_domain
    ids = shelter_pets_data.get_pet_assignee_ids(obj["id"])
    return [users_domain.get_user(uid) for uid in ids]


def get_assigned_shelter_people(obj, info):
    import domain.shelter_people as shelter_people_domain
    ids = shelter_pets_data.get_pet_assignee_shelter_person_ids(obj["id"])
    return [shelter_people_domain.get_shelter_person(pid) for pid in ids]


def set_shelter_pet_published(shelter_pet_id, is_published):
    """Gates public storefront/donation visibility for a shelter pet."""
    logger.domain(f"shelter_pet_id: {shelter_pet_id} is_published: {is_published}")
    try:
        return shelter_pets_data.update_shelter_pet(
            shelter_pet_id, {"is_published": bool(is_published)}
        )
    except Exception as e:
        logger.error(e)
        raise e


def set_shelter_pet_assignees(shelter_pet_id, user_ids, shelter_person_ids=None):
    """Replace-all assignment of shelter members to a pet. Every user must
    hold a role on the pet's shelter; every shelter_person must belong to it."""
    import domain.shelter_people as shelter_people_domain
    logger.domain(
        f"shelter_pet_id: {shelter_pet_id} user_ids: {stringify(user_ids)} "
        f"shelter_person_ids: {stringify(shelter_person_ids)}"
    )
    try:
        sp = shelter_pets_data.get_shelter_pet(shelter_pet_id)
        shelter_id = sp["shelter_id"]
        for uid in dict.fromkeys(user_ids or []):
            if not shelter_roles_data.get_roles_for_user_on_shelter(uid, shelter_id):
                raise BadRequest(f"user {uid} is not a member of shelter {shelter_id}")
        for pid in dict.fromkeys(shelter_person_ids or []):
            person = shelter_people_domain.get_shelter_person(pid)
            if person is None or person["shelter_id"] != shelter_id:
                raise BadRequest(f"shelter_person {pid} does not belong to shelter {shelter_id}")
        shelter_pets_data.set_pet_assignees(shelter_pet_id, user_ids, shelter_person_ids)
        return shelter_pets_data.get_shelter_pet(shelter_pet_id)
    except Exception as e:
        logger.error(e)
        raise e


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


def create_shelter_pets_with_data(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        shelter_id = data.get('shelter_id')
        shelter = shelters_domain.get_shelter(shelter_id)
        if shelter is None:
            raise NotFoundError(f'no shelter found with id {shelter_id}')
        pets_in = data.get('pets') or []
        if not pets_in:
            raise BadRequest('pets must not be empty')
        pets = []
        for p in pets_in:
            name = p.get('name')
            birthday = p.get('birthday')
            if not name:
                raise BadRequest('pet name is required')
            if not birthday:
                raise BadRequest('pet birthday is required')
            neutered = p.get('neutered')
            pets.append({
                **p,
                'name': name,
                'birthday': birthday,
                'gender': p.get('gender') or 'NOT_SAID',
                'breed': p.get('breed') or 'cross breed',
                'neutered': True if neutered is None else neutered,
            })
        return shelter_pets_data.create_shelter_pets_with_data(shelter_id, pets)
    except Exception as e:
        logger.error(e)
        raise e


def change_shelter(data, actor_id=None):
    logger.domain(f"data: {stringify(data)}")
    try:
        pet_id = data.get('pet_id')
        shelter_id_from = data.get('shelter_id_from')
        shelter_id_to = data.get('shelter_id_to')
        if shelter_id_from == shelter_id_to:
            raise BadRequest('shelter_id_from and shelter_id_to must differ')
        pet = pets_domain.get_pet(pet_id)
        if pet is None:
            raise NotFoundError(f'no pet found with id {pet_id}')
        shelter_from = shelters_domain.get_shelter(shelter_id_from)
        if shelter_from is None:
            raise NotFoundError(f'no shelter found with id {shelter_id_from}')
        shelter_to = shelters_domain.get_shelter(shelter_id_to)
        if shelter_to is None:
            raise NotFoundError(f'no shelter found with id {shelter_id_to}')
        return shelter_pets_data.change_shelter(pet_id, shelter_id_from, shelter_id_to, actor_id)
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
