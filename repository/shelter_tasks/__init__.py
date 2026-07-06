import uuid
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_tasks.models import ShelterTask, TaskStatus
from repository.query_builder import build_query, build_count


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.strptime(value, DATE_FMT)


def create_shelter_task(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        shelter_task = ShelterTask(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            shelter_id=data["shelter_id"],
            shelter_pet_id=data.get("shelter_pet_id"),
            shelter_box_id=data.get("shelter_box_id"),
            task_type=data["task_type"],
            area=data.get("area"),
            status=data.get("status") or TaskStatus.PENDING.name,
            assigned_to_id=data.get("assigned_to_id"),
            scheduled_at=_parse_dt(data.get("scheduled_at")),
            is_recurring=data.get("is_recurring") or False,
            recurrence_rule=data.get("recurrence_rule"),
            template_id=data.get("template_id"),
            notes=data.get("notes"),
        )
        db.session.add(shelter_task)
        db.session.commit()
        return shelter_task.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def update_shelter_task(id, data):
    logger.repository(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        query = db.session.query(ShelterTask).filter(ShelterTask.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_task found with id: {id}")
        old = query.first().to_dict()
        payload = dict(data)
        if "scheduled_at" in payload:
            payload["scheduled_at"] = _parse_dt(payload.get("scheduled_at"))
        if "completed_at" in payload:
            payload["completed_at"] = _parse_dt(payload.get("completed_at"))
        query.update(payload)
        db.session.commit()
        return {**old, **query.first().to_dict()}
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_shelter_task(id):
    logger.repository(f"id: {id}")
    try:
        model = ShelterTask.query.get(id)
        if not model:
            raise NotFoundError(f"no shelter_task found with id: {id}")
        return model.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_tasks(common_search):
    try:
        query = build_query(
            table="shelter_tasks",
            ordering=common_search["ordering"],
            filters=common_search["filters"],
            pagination=common_search["pagination"],
        )
        manager = select(ShelterTask).from_statement(text(query))
        results = db.session.execute(manager).scalars()
        return [row.to_dict() for row in results]
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="shelter_tasks", filters=common_search["filters"])
        result = db.session.execute(query).first()
        return result[0] if result is not None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest("malformed variables_fields")
    except Exception as e:
        logger.error(e)
        raise e


def count_by_status(shelter_id, status_names):
    statuses = [TaskStatus[n] for n in status_names]
    return db.session.query(ShelterTask).filter(
        ShelterTask.shelter_id == shelter_id,
        ShelterTask.status.in_(statuses),
    ).count()


def count_overdue(shelter_id, now):
    return db.session.query(ShelterTask).filter(
        ShelterTask.shelter_id == shelter_id,
        ShelterTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
        ShelterTask.scheduled_at.isnot(None),
        ShelterTask.scheduled_at < now,
    ).count()


def count_completed_between(shelter_id, start, end):
    return db.session.query(ShelterTask).filter(
        ShelterTask.shelter_id == shelter_id,
        ShelterTask.status == TaskStatus.COMPLETED,
        ShelterTask.completed_at >= start,
        ShelterTask.completed_at < end,
    ).count()


def get_recurring_templates():
    models = db.session.query(ShelterTask).filter(ShelterTask.is_recurring == True).all()
    return [m.to_dict() for m in models]


def has_occurrence_on(template_id, day_start, day_end):
    return db.session.query(ShelterTask).filter(
        ShelterTask.template_id == template_id,
        ShelterTask.scheduled_at >= day_start,
        ShelterTask.scheduled_at < day_end,
    ).count() > 0


def delete_shelter_task(id):
    logger.repository(f"id: {id} remove")
    try:
        query = db.session.query(ShelterTask).filter(ShelterTask.id == id)
        if not query.first():
            raise NotFoundError(f"no shelter_task found with id: {id}")
        query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e
