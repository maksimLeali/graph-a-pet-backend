import uuid
from datetime import datetime
from sqlalchemy import select, text, func
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_inventory_items.models import ShelterInventoryItem
from repository.shelter_inventory_movements.models import ShelterInventoryMovement
from repository.query_builder import build_query, build_count
from utils.dates import utc_now


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def create_shelter_inventory_item(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = utc_now()
        item = ShelterInventoryItem(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            shelter_id=data["shelter_id"],
            name=data["name"],
            category=data.get("category"),
            unit=data.get("unit"),
            minimum_threshold=data.get("minimum_threshold"),
            notes=data.get("notes"),
        )
        db.session.add(item)
        db.session.commit()
        return item.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_inventory_item(id, data):
    logger.repository(f"id: {id}\ndata: {stringify(data)}")
    try:
        query = db.session.query(ShelterInventoryItem).filter(ShelterInventoryItem.id == id)
        if not query.first():
            raise NotFoundError(f"no inventory item found with id: {id}")
        old = query.first().to_dict()
        query.update(dict(data))
        db.session.commit()
        return {**old, **query.first().to_dict()}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_inventory_item(id):
    logger.repository(f"id: {id}")
    try:
        model = ShelterInventoryItem.query.get(id)
        if not model:
            raise NotFoundError(f"no inventory item found with id: {id}")
        return model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def get_items_by_shelter(shelter_id):
    models = db.session.query(ShelterInventoryItem).filter(
        ShelterInventoryItem.shelter_id == shelter_id
    ).all()
    return [m.to_dict() for m in models]


def get_current_quantity(item_id):
    total = db.session.query(
        func.coalesce(func.sum(ShelterInventoryMovement.quantity), 0)
    ).filter(ShelterInventoryMovement.item_id == item_id).scalar()
    return float(total or 0)


def count_movements(item_id):
    return db.session.query(ShelterInventoryMovement).filter(
        ShelterInventoryMovement.item_id == item_id
    ).count()


def archive_shelter_inventory_item(id, user_id):
    logger.repository(f"id: {id} archive by {user_id}")
    try:
        query = db.session.query(ShelterInventoryItem).filter(ShelterInventoryItem.id == id)
        if not query.first():
            raise NotFoundError(f"no inventory item found with id: {id}")
        query.update({
            "is_active": False,
            "archived_at": utc_now(),
            "archived_by_id": user_id,
        })
        db.session.commit()
        return query.first().to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_inventory_items(common_search):
    try:
        query = build_query(
            table="shelter_inventory_items",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterInventoryItem).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_inventory_items", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_inventory_item(id):
    logger.repository(f"id: {id} remove")
    try:
        query = db.session.query(ShelterInventoryItem).filter(ShelterInventoryItem.id == id)
        if not query.first():
            raise NotFoundError(f"no inventory item found with id: {id}")
        query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e
