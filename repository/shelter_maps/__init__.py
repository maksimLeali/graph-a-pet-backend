import uuid
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_maps.models import ShelterMap, MapUnit
from repository.shelter_areas.models import ShelterArea
from repository.shelter_boxes.models import ShelterBox
from repository.shelter_map_elements.models import ShelterMapElement
from repository.query_builder import build_query, build_count


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def create_shelter_map(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        shelter_map = ShelterMap(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            shelter_id=data["shelter_id"],
            name=data.get("name"),
            width=data.get("width"),
            height=data.get("height"),
            unit=data.get("unit") or MapUnit.METERS.name,
            background_media_id=data.get("background_media_id"),
        )
        db.session.add(shelter_map)
        db.session.commit()
        return shelter_map.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_map(id, data):
    logger.repository(f"id: {id}\ndata: {stringify(data)}")
    try:
        query = db.session.query(ShelterMap).filter(ShelterMap.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_map found with id: {id}")
        old = query.first().to_dict()
        query.update(dict(data))
        db.session.commit()
        return {**old, **query.first().to_dict()}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_map(id):
    logger.repository(f"id: {id}")
    try:
        model = ShelterMap.query.get(id)
        if not model:
            raise NotFoundError(f"no shelter_map found with id: {id}")
        return model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def get_maps_by_shelter(shelter_id):
    models = db.session.query(ShelterMap).filter(ShelterMap.shelter_id == shelter_id).all()
    return [m.to_dict() for m in models]


def get_shelter_maps(common_search):
    try:
        query = build_query(
            table="shelter_maps",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterMap).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_maps", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter_map(id):
    logger.repository(f"id: {id} remove")
    try:
        query = db.session.query(ShelterMap).filter(ShelterMap.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_map found with id: {id}")
        query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


AREA_FIELDS = ["name", "area_type", "x", "y", "width", "height", "color"]
BOX_FIELDS = ["area_id", "label", "x", "y", "width", "height", "rotation", "capacity"]
ELEMENT_FIELDS = ["element_type", "x", "y", "width", "height", "rotation", "color", "label"]


def save_layout(map_id, data):
    """Upsert atomico di aree e box + delete per id, un solo commit (rollback totale su errore)."""
    logger.repository(f"map_id: {map_id} data: {stringify(data)}")
    try:
        # --- aree ---
        for a in (data.get("areas") or []):
            if a.get("id"):
                model = db.session.query(ShelterArea).filter(ShelterArea.id == a["id"]).first()
                if not model:
                    raise NotFoundError(f'no shelter_area found with id: {a["id"]}')
                for f in AREA_FIELDS:
                    if f in a:
                        setattr(model, f, a[f])
            else:
                db.session.add(ShelterArea(
                    id=f"{uuid.uuid4()}",
                    created_at=datetime.today().strftime(DATE_FMT),
                    map_id=map_id,
                    **{f: a.get(f) for f in AREA_FIELDS},
                ))

        # --- box ---
        for b in (data.get("boxes") or []):
            if b.get("id"):
                model = db.session.query(ShelterBox).filter(ShelterBox.id == b["id"]).first()
                if not model:
                    raise NotFoundError(f'no shelter_box found with id: {b["id"]}')
                for f in BOX_FIELDS:
                    if f in b:
                        setattr(model, f, b[f])
            else:
                db.session.add(ShelterBox(
                    id=f"{uuid.uuid4()}",
                    created_at=datetime.today().strftime(DATE_FMT),
                    map_id=map_id,
                    area_id=b.get("area_id"),
                    label=b["label"],
                    x=b.get("x"), y=b.get("y"), width=b.get("width"), height=b.get("height"),
                    rotation=b.get("rotation") if b.get("rotation") is not None else 0,
                    capacity=b.get("capacity") if b.get("capacity") is not None else 1,
                ))

        # --- elementi ---
        for el in (data.get("elements") or []):
            if el.get("id"):
                model = db.session.query(ShelterMapElement).filter(ShelterMapElement.id == el["id"]).first()
                if not model:
                    raise NotFoundError(f'no map element found with id: {el["id"]}')
                for f in ELEMENT_FIELDS:
                    if f in el:
                        setattr(model, f, el[f])
            else:
                db.session.add(ShelterMapElement(
                    id=f"{uuid.uuid4()}",
                    created_at=datetime.today().strftime(DATE_FMT),
                    map_id=map_id,
                    element_type=el["element_type"],
                    x=el.get("x"), y=el.get("y"), width=el.get("width"), height=el.get("height"),
                    rotation=el.get("rotation") if el.get("rotation") is not None else 0,
                    color=el.get("color"), label=el.get("label"),
                ))

        # --- delete ---
        for area_id in (data.get("deleted_area_ids") or []):
            db.session.query(ShelterArea).filter(ShelterArea.id == area_id).delete()
        for box_id in (data.get("deleted_box_ids") or []):
            db.session.query(ShelterBox).filter(ShelterBox.id == box_id).delete()
        for element_id in (data.get("deleted_element_ids") or []):
            db.session.query(ShelterMapElement).filter(ShelterMapElement.id == element_id).delete()

        db.session.commit()
        return get_shelter_map(map_id)
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e
