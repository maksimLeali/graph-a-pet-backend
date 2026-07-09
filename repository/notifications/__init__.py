import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from repository import db
from api.errors import NotFoundError
from utils.logger import logger, stringify
from repository.notifications.models import (
    Notification,
    NotificationStatus,
)

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"

# statuses visible in the inbox (DISMISSED/EXPIRED are hidden but not deleted)
VISIBLE_STATUSES = [NotificationStatus.UNREAD, NotificationStatus.READ]


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.strptime(value, DATE_FMT)


def create_notification(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        notification = Notification(
            id=f"{uuid.uuid4()}",
            created_at=today.strftime(DATE_FMT),
            user_id=data["user_id"],
            type=data["type"],
            status=data.get("status") or NotificationStatus.UNREAD.name,
            priority=data.get("priority") or "NORMAL",
            title=data["title"],
            message=data.get("message"),
            entity_type=data.get("entity_type"),
            entity_id=data.get("entity_id"),
            action_url=data.get("action_url"),
            actor_user_id=data.get("actor_user_id"),
            shelter_id=data.get("shelter_id"),
            pet_id=data.get("pet_id"),
            payload=data.get("payload"),
            dedupe_key=data.get("dedupe_key"),
            scheduled_at=_parse_dt(data.get("scheduled_at")),
            expires_at=_parse_dt(data.get("expires_at")),
        )
        db.session.add(notification)
        db.session.commit()
        return notification.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def create_if_absent(data):
    """Idempotent insert keyed on dedupe_key. Returns the row, or None if a
    notification with the same dedupe_key already exists (unique violation)."""
    key = data.get("dedupe_key")
    if key and get_by_dedupe_key(key) is not None:
        return None
    try:
        return create_notification(data)
    except IntegrityError as e:
        db.session.rollback()
        logger.repository(f"duplicate notification skipped: {e}")
        return None


def get_by_dedupe_key(dedupe_key):
    model = db.session.query(Notification).filter(
        Notification.dedupe_key == dedupe_key
    ).first()
    return model.to_dict() if model else None


def get_notification(id):
    model = Notification.query.get(id)
    if not model:
        raise NotFoundError(f"no notification found with id: {id}")
    return model.to_dict()


def list_my_notifications(user_id, pagination):
    page = pagination.get("page", 0)
    page_size = pagination.get("page_size", 20)
    query = db.session.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.status.in_(VISIBLE_STATUSES),
    ).order_by(Notification.created_at.desc())
    total = query.count()
    rows = query.offset(page * page_size).limit(page_size).all()
    return [r.to_dict() for r in rows], total


def count_unread(user_id):
    return db.session.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.status == NotificationStatus.UNREAD,
    ).count()


def mark_as_read(id, user_id):
    try:
        notification = db.session.query(Notification).filter(
            Notification.id == id,
            Notification.user_id == user_id,
        ).first()
        if not notification:
            raise NotFoundError(f"no notification found with id: {id}")
        if notification.status == NotificationStatus.UNREAD:
            notification.status = NotificationStatus.READ
            notification.read_at = datetime.today()
            db.session.commit()
        return notification.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def mark_all_as_read(user_id):
    try:
        now = datetime.today()
        db.session.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.UNREAD,
        ).update(
            {Notification.status: NotificationStatus.READ, Notification.read_at: now},
            synchronize_session=False,
        )
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def dismiss(id, user_id):
    try:
        notification = db.session.query(Notification).filter(
            Notification.id == id,
            Notification.user_id == user_id,
        ).first()
        if not notification:
            raise NotFoundError(f"no notification found with id: {id}")
        notification.status = NotificationStatus.DISMISSED
        notification.dismissed_at = datetime.today()
        db.session.commit()
        return notification.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


# --- cron sources (read the real entities; notifications only point to them) ---
def get_owner_ids_for_pet(pet_id):
    from repository.ownerships.models import Ownership
    rows = db.session.query(Ownership.user_id).filter(
        Ownership.pet_id == pet_id,
        Ownership.user_id.isnot(None),
    ).all()
    return [r[0] for r in rows]


def get_due_treatments(day_start, day_end):
    """Vaccines / operations / antiparasitics scheduled within [day_start, day_end),
    joined to their pet via the health card."""
    from repository.treatments.models import Treatment, TreatmentType
    from repository.health_cards.models import HealthCard
    from repository.pets.models import Pet
    reminder_types = [
        TreatmentType.VACCINE,
        TreatmentType.OPERATION,
        TreatmentType.ANTIPARASITIC,
    ]
    rows = (
        db.session.query(
            Treatment.id, Treatment.name, Treatment.type,
            Pet.id, Pet.name,
        )
        .join(HealthCard, Treatment.health_card_id == HealthCard.id)
        .join(Pet, HealthCard.pet_id == Pet.id)
        .filter(
            Treatment.type.in_(reminder_types),
            Treatment.date >= day_start,
            Treatment.date < day_end,
        )
        .all()
    )
    return [
        {
            "treatment_id": r[0],
            "treatment_name": r[1],
            "treatment_type": r[2].name if r[2] else None,
            "pet_id": r[3],
            "pet_name": r[4],
        }
        for r in rows
    ]


def get_pets_with_birthday(month, day):
    from sqlalchemy import extract
    from repository.pets.models import Pet
    rows = db.session.query(Pet.id, Pet.name).filter(
        Pet.birthday.isnot(None),
        extract('month', Pet.birthday) == month,
        extract('day', Pet.birthday) == day,
    ).all()
    return [{"pet_id": r[0], "pet_name": r[1]} for r in rows]
