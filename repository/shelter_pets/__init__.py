import uuid
from datetime import datetime
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text
from api.errors import BadRequest, NotFoundError
from repository import db, schema
from utils.logger import logger, stringify
from repository.shelter_pets.models import ShelterPet
from repository.pets.models import Pet
from repository.query_builder import build_query, build_count, build_where
from utils.dates import utc_now


def create_shelter_pet(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = utc_now()
        shelter_pet = ShelterPet(
            id=f"{uuid.uuid4()}",
            shelter_id=data["shelter_id"],
            pet_id=data["pet_id"],
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        )
        db.session.add(shelter_pet)
        db.session.commit()
        return shelter_pet.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def create_shelter_pets(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = utc_now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        shelter_id = data["shelter_id"]
        shelter_pets = [
            ShelterPet(
                id=f"{uuid.uuid4()}",
                shelter_id=shelter_id,
                pet_id=pet_id,
                created_at=today,
            )
            for pet_id in data["pet_ids"]
        ]
        db.session.add_all(shelter_pets)
        db.session.commit()
        return [sp.to_dict() for sp in shelter_pets]
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def create_shelter_pets_with_data(shelter_id, pets):
    logger.repository(f"shelter_id: {shelter_id} count: {len(pets)}")
    try:
        today = utc_now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        created = []
        for p in pets:
            pet = Pet(
                id=f"{uuid.uuid4()}",
                name=p.get("name"),
                birthday=p.get("birthday"),
                neutered=p.get("neutered"),
                gender=p.get("gender"),
                breed=p.get("breed"),
                coat_length=p.get("coat_length"),
                temperament=p.get("temperament"),
                weight_kg=p.get("weight_kg"),
                chip_code=p.get("chip_code"),
                created_at=today,
            )
            db.session.add(pet)
            shelter_pet = ShelterPet(
                id=f"{uuid.uuid4()}",
                shelter_id=shelter_id,
                pet_id=pet.id,
                created_at=today,
            )
            db.session.add(shelter_pet)
            created.append(shelter_pet)
        db.session.commit()
        return [sp.to_dict() for sp in created]
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_pet(id, data):
    logger.repository(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        shelter_pet_model = db.session.query(ShelterPet).filter(ShelterPet.id == id)
        if not shelter_pet_model.first():
            raise NotFoundError(f"no shelter_pet found with id: {id}")
        shelter_pet_old = shelter_pet_model.first().to_dict()
        shelter_pet_model.update(data)
        db.session.commit()
        shelter_pet = {**shelter_pet_old, **shelter_pet_model.first().to_dict()}
        logger.check(f'shelter_pet: {stringify(shelter_pet)}')
        return shelter_pet
    except Exception as e:
        logger.error(e)
        raise e


def change_shelter(pet_id, shelter_id_from, shelter_id_to, actor_id=None):
    """Transfer a pet between shelters atomically (single commit):
      1. locate the active membership in the source shelter
      2. close any active box occupancy
      3. cancel planned / in-progress walks
      4. cancel pending / in-progress tasks tied to the membership
      5. deactivate the old ShelterPet
      6. create a new active ShelterPet in the destination
      7. write an audit log
    Any failure rolls the whole thing back — no ambiguous pet state.
    """
    from repository.shelter_box_occupancies.models import ShelterBoxOccupancy
    from repository.shelter_walks.models import ShelterWalk, ShelterWalkStatus
    from repository.shelter_tasks.models import ShelterTask, TaskStatus
    logger.repository(
        f"transfer pet_id: {pet_id} from {shelter_id_from} to {shelter_id_to}"
    )
    try:
        now = utc_now()
        now_s = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        old_sp = db.session.query(ShelterPet).filter(
            ShelterPet.pet_id == pet_id,
            ShelterPet.shelter_id == shelter_id_from,
            ShelterPet.is_active == True,
        ).first()
        if not old_sp:
            raise NotFoundError(
                f"no active shelter_pet found for pet {pet_id} in shelter {shelter_id_from}"
            )

        # 2. close active box occupancy for this membership
        db.session.query(ShelterBoxOccupancy).filter(
            ShelterBoxOccupancy.shelter_pet_id == old_sp.id,
            ShelterBoxOccupancy.exited_at.is_(None),
        ).update(
            {"exited_at": now, "moved_by_id": actor_id, "reason": "shelter transfer"},
            synchronize_session=False,
        )

        # 3. cancel planned / in-progress walks
        db.session.query(ShelterWalk).filter(
            ShelterWalk.shelter_pet_id == old_sp.id,
            ShelterWalk.status.in_([ShelterWalkStatus.PLANNED, ShelterWalkStatus.IN_PROGRESS]),
        ).update({"status": ShelterWalkStatus.CANCELLED}, synchronize_session=False)

        # 4. cancel pending / in-progress tasks
        db.session.query(ShelterTask).filter(
            ShelterTask.shelter_pet_id == old_sp.id,
            ShelterTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
        ).update({"status": TaskStatus.CANCELLED}, synchronize_session=False)

        # 5. deactivate old membership
        old_sp.is_active = False
        old_sp.left_at = now
        old_sp.updated_at = now_s

        # 6. create new active membership in destination
        new_sp = ShelterPet(
            id=f"{uuid.uuid4()}",
            shelter_id=shelter_id_to,
            pet_id=pet_id,
            is_active=True,
            created_at=now_s,
        )
        db.session.add(new_sp)

        db.session.commit()
        # 7. audit log
        logger.check(
            f"AUDIT pet_transfer pet={pet_id} from={shelter_id_from} "
            f"to={shelter_id_to} actor={actor_id} old_sp={old_sp.id} new_sp={new_sp.id}"
        )
        return new_sp.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def count_in_shelter(shelter_id):
    return db.session.query(ShelterPet).filter(
        ShelterPet.shelter_id == shelter_id,
        ShelterPet.is_active == True,
    ).count()


def get_shelter_pets(common_search):
    try:
        query = build_query(table="shelter_pets", ordering=common_search["ordering"], filters=common_search['filters'], pagination=common_search['pagination'])
        manager = select(ShelterPet).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_filtered_shelter_pets(filters):
    results = select(ShelterPet).from_statement(text(
        f"\
            SELECT  * \
            FROM { (schema + '.') if schema else '' }shelter_pets \
            { '' if len(filters)== 0 else build_where(filters) } \
        "))
    shelter_pets = db.session.execute(results).scalars()
    return [shelter_pet.to_dict() for shelter_pet in shelter_pets]


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_pets", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_pet(id):
    logger.repository(f"id: {id}")
    try:
        shelter_pet_model = ShelterPet.query.get(id)
        if not shelter_pet_model:
            raise NotFoundError(f"no shelter_pet found with id: {id}")
        return shelter_pet_model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_pet(id):
    logger.repository(f"id: {id}  remove")
    try:
        shelter_pet_model = db.session.query(ShelterPet).filter(ShelterPet.id == id)
        if not shelter_pet_model:
            raise NotFoundError(f"no shelter_pet found with id: {id}")
        shelter_pet_model.delete()
        db.session.commit()
        logger.check(f"deleted {id}")
    except Exception as e:
        logger.error(e)
        raise e
