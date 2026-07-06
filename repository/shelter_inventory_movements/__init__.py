import uuid
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_inventory_movements.models import ShelterInventoryMovement
from repository.query_builder import build_query, build_count


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def create_shelter_inventory_movement(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        movement = ShelterInventoryMovement(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            item_id=data["item_id"],
            movement_type=data["movement_type"],
            quantity=data["quantity"],
            registered_by_id=data["registered_by_id"],
            notes=data.get("notes"),
        )
        db.session.add(movement)
        db.session.commit()
        return movement.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_inventory_movement(id):
    logger.repository(f"id: {id}")
    try:
        model = ShelterInventoryMovement.query.get(id)
        if not model:
            raise NotFoundError(f"no inventory movement found with id: {id}")
        return model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def get_movements_by_item(item_id):
    models = db.session.query(ShelterInventoryMovement).filter(
        ShelterInventoryMovement.item_id == item_id
    ).order_by(ShelterInventoryMovement.created_at.desc()).all()
    return [m.to_dict() for m in models]


def get_shelter_inventory_movements(common_search):
    try:
        query = build_query(
            table="shelter_inventory_movements",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterInventoryMovement).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_inventory_movements", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e
