import uuid
from datetime import datetime
from sqlalchemy import select, text, or_, and_
from sqlalchemy.exc import ProgrammingError
from api.errors import BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_tasks.models import ShelterTask, ShelterTaskAssignee, TaskStatus
from repository.query_builder import build_query, build_count
from utils.dates import utc_now


DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.strptime(value, DATE_FMT)


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    from datetime import date as _date
    if isinstance(value, _date):
        return value
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def create_shelter_task(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = utc_now()
        shelter_task = ShelterTask(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            shelter_id=data["shelter_id"],
            shelter_pet_id=data.get("shelter_pet_id"),
            shelter_box_id=data.get("shelter_box_id"),
            task_type=data["task_type"],
            area=data.get("area"),
            status=data.get("status") or TaskStatus.PENDING.name,
            scheduled_at=_parse_dt(data.get("scheduled_at")),
            scheduled_date=_parse_date(data.get("scheduled_date") or data.get("scheduled_at")),
            is_recurring=data.get("is_recurring") or False,
            recurrence_freq=data.get("recurrence_freq"),
            recurrence_interval=data.get("recurrence_interval"),
            recurrence_weekdays=data.get("recurrence_weekdays"),
            recurrence_week_ordinal=data.get("recurrence_week_ordinal"),
            recurrence_time=data.get("recurrence_time"),
            recurrence_start=_parse_dt(data.get("recurrence_start")),
            template_id=data.get("template_id"),
            notes=data.get("notes"),
        )
        db.session.add(shelter_task)
        db.session.commit()
        if "assignee_ids" in data or "assignee_shelter_person_ids" in data:
            set_task_assignees(
                shelter_task.id,
                data.get("assignee_ids"),
                data.get("assignee_shelter_person_ids"),
            )
        return shelter_task.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_task_assignee_ids(task_id):
    rows = db.session.query(ShelterTaskAssignee.user_id).filter(
        ShelterTaskAssignee.task_id == task_id,
        ShelterTaskAssignee.user_id.isnot(None),
    ).all()
    return [r[0] for r in rows]


def get_task_assignee_shelter_person_ids(task_id):
    rows = db.session.query(ShelterTaskAssignee.shelter_person_id).filter(
        ShelterTaskAssignee.task_id == task_id,
        ShelterTaskAssignee.shelter_person_id.isnot(None),
    ).all()
    return [r[0] for r in rows]


def set_task_assignees(task_id, user_ids, shelter_person_ids=None):
    """Replace-all: the given user_ids/shelter_person_ids become the exact
    assignee set (shelter_person_ids are contacts/volunteers without an app
    account)."""
    logger.repository(
        f"task_id: {task_id} assignees: {stringify(user_ids)} "
        f"shelter_person_assignees: {stringify(shelter_person_ids)}"
    )
    try:
        db.session.query(ShelterTaskAssignee).filter(
            ShelterTaskAssignee.task_id == task_id
        ).delete()
        for uid in dict.fromkeys(user_ids or []):
            db.session.add(ShelterTaskAssignee(
                id=f"{uuid.uuid4()}",
                created_at=utc_now().strftime(DATE_FMT),
                task_id=task_id,
                user_id=uid,
            ))
        for pid in dict.fromkeys(shelter_person_ids or []):
            db.session.add(ShelterTaskAssignee(
                id=f"{uuid.uuid4()}",
                created_at=utc_now().strftime(DATE_FMT),
                task_id=task_id,
                shelter_person_id=pid,
            ))
        db.session.commit()
        return get_task_assignee_ids(task_id), get_task_assignee_shelter_person_ids(task_id)
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
        assignee_ids = payload.pop("assignee_ids", None)
        assignee_shelter_person_ids = payload.pop("assignee_shelter_person_ids", None)
        if "scheduled_at" in payload:
            payload["scheduled_at"] = _parse_dt(payload.get("scheduled_at"))
        if "completed_at" in payload:
            payload["completed_at"] = _parse_dt(payload.get("completed_at"))
        if "skipped_at" in payload:
            payload["skipped_at"] = _parse_dt(payload.get("skipped_at"))
        if "scheduled_date" in payload:
            payload["scheduled_date"] = _parse_date(payload.get("scheduled_date"))
        if "recurrence_start" in payload:
            payload["recurrence_start"] = _parse_dt(payload.get("recurrence_start"))
        if payload:
            query.update(payload)
        db.session.commit()
        if assignee_ids is not None or assignee_shelter_person_ids is not None:
            final_user_ids = (
                assignee_ids if assignee_ids is not None else get_task_assignee_ids(id)
            )
            final_shelter_person_ids = (
                assignee_shelter_person_ids
                if assignee_shelter_person_ids is not None
                else get_task_assignee_shelter_person_ids(id)
            )
            set_task_assignees(id, final_user_ids, final_shelter_person_ids)
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


def get_tasks_assigned_to_user(user_id, start, end):
    """Materialized (non-template) tasks assigned to user_id, any status
    (pending/overdue/completed/skipped/cancelled), either scheduled within
    [start, end) or unscheduled (no due date set — still a to-do, so it must
    not be silently dropped)."""
    rows = db.session.query(ShelterTask).join(
        ShelterTaskAssignee, ShelterTaskAssignee.task_id == ShelterTask.id
    ).filter(
        ShelterTaskAssignee.user_id == user_id,
        ShelterTask.is_recurring == False,
        or_(
            ShelterTask.scheduled_at.is_(None),
            and_(ShelterTask.scheduled_at >= start, ShelterTask.scheduled_at < end),
        ),
    ).order_by(ShelterTask.scheduled_at.asc()).all()
    return [r.to_dict() for r in rows]


def get_operational_tasks(shelter_id, week_start, week_end, restrict_to_user_id=None):
    """Operational (non-history) tasks view for a shelter:
    - recurring templates are always visible (they're a rule, not a to-do
      bound to a date);
    - undated one-off tasks are visible while still open (pending/in
      progress) — same "don't silently drop" convention as elsewhere;
    - dated tasks (instances or one-off) are visible if scheduled within the
      current week, whatever their status — closed tasks from previous weeks
      stay in the DB for future history screens, just not shown here.
    """
    week_start_date = week_start.date() if hasattr(week_start, "date") else week_start
    week_end_date = week_end.date() if hasattr(week_end, "date") else week_end
    query = db.session.query(ShelterTask).filter(
        ShelterTask.shelter_id == shelter_id,
    )
    if restrict_to_user_id:
        import repository.shelter_people as shelter_people_data
        person_ids = shelter_people_data.get_person_ids_for_user(
            restrict_to_user_id, shelter_id)
        # volunteers see unassigned tasks plus tasks assigned to them
        # (directly or through their linked shelter_person)
        has_any_assignee = db.session.query(ShelterTaskAssignee.id).filter(
            ShelterTaskAssignee.task_id == ShelterTask.id
        ).exists()
        mine_conds = [ShelterTaskAssignee.user_id == restrict_to_user_id]
        if person_ids:
            mine_conds.append(ShelterTaskAssignee.shelter_person_id.in_(person_ids))
        assigned_to_me = db.session.query(ShelterTaskAssignee.id).filter(
            ShelterTaskAssignee.task_id == ShelterTask.id,
            or_(*mine_conds),
        ).exists()
        query = query.filter(or_(~has_any_assignee, assigned_to_me))
    rows = query.order_by(ShelterTask.scheduled_at.asc()).all()
    return [r.to_dict() for r in rows]


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


def count_skipped_between(shelter_id, start, end):
    return db.session.query(ShelterTask).filter(
        ShelterTask.shelter_id == shelter_id,
        ShelterTask.status == TaskStatus.SKIPPED,
        ShelterTask.skipped_at >= start,
        ShelterTask.skipped_at < end,
    ).count()


def count_all(shelter_id):
    """Task operative (esclude i template ricorrenti)."""
    return db.session.query(ShelterTask).filter(
        ShelterTask.shelter_id == shelter_id,
        ShelterTask.is_recurring == False,
    ).count()


def count_recurring(shelter_id):
    """Task periodiche (template ricorrenti)."""
    return db.session.query(ShelterTask).filter(
        ShelterTask.shelter_id == shelter_id,
        ShelterTask.is_recurring == True,
    ).count()


def count_due_between(shelter_id, start, end):
    """Task da fare (pending/in progress) programmate nel range."""
    return db.session.query(ShelterTask).filter(
        ShelterTask.shelter_id == shelter_id,
        ShelterTask.is_recurring == False,
        ShelterTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
        ShelterTask.scheduled_at.isnot(None),
        ShelterTask.scheduled_at >= start,
        ShelterTask.scheduled_at < end,
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


def has_instance_on_date(template_id, scheduled_date):
    """Idempotency check for the cron: does an instance already exist for this
    template on this calendar day (matches the ux_shelter_task unique index)?"""
    return db.session.query(ShelterTask).filter(
        ShelterTask.template_id == template_id,
        ShelterTask.scheduled_date == _parse_date(scheduled_date),
    ).count() > 0


def create_task_instance(data):
    """Create a materialized instance; returns the row, or None if a concurrent
    run already inserted it (unique constraint violation is swallowed)."""
    from sqlalchemy.exc import IntegrityError
    try:
        return create_shelter_task(data)
    except IntegrityError as e:
        db.session.rollback()
        logger.repository(f"duplicate task instance skipped: {e}")
        return None


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
