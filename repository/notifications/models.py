from enum import Enum
from repository import db, Base
from sqlalchemy.dialects.postgresql import JSONB


class NotificationType(Enum):
    TREATMENT_REMINDER = "TREATMENT_REMINDER"
    PET_OWNERSHIP_INVITE = "PET_OWNERSHIP_INVITE"
    SHELTER_INVITE = "SHELTER_INVITE"
    SHELTER_TASK_INSTANCE = "SHELTER_TASK_INSTANCE"
    SHELTER_JOIN_REQUEST = "SHELTER_JOIN_REQUEST"
    PET_BIRTHDAY = "PET_BIRTHDAY"
    SHELTER_OWNERSHIP_TRANSFER = "SHELTER_OWNERSHIP_TRANSFER"
    SHELTER_CLAIM_REQUEST = "SHELTER_CLAIM_REQUEST"


class NotificationStatus(Enum):
    UNREAD = "UNREAD"
    READ = "READ"
    DISMISSED = "DISMISSED"
    EXPIRED = "EXPIRED"


class NotificationPriority(Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class NotificationEntityType(Enum):
    PET = "PET"
    TREATMENT = "TREATMENT"
    OWNERSHIP = "OWNERSHIP"
    SHELTER = "SHELTER"
    SHELTER_INVITE = "SHELTER_INVITE"
    SHELTER_TASK = "SHELTER_TASK"
    SHELTER_JOIN_REQUEST = "SHELTER_JOIN_REQUEST"
    SHELTER_OWNERSHIP_TRANSFER = "SHELTER_OWNERSHIP_TRANSFER"
    SHELTER_CLAIM_REQUEST = "SHELTER_CLAIM_REQUEST"


class Notification(Base):
    __tablename__ = 'notifications'

    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    status = db.Column(db.Enum(NotificationStatus), nullable=False,
                       default=NotificationStatus.UNREAD.name, index=True)
    priority = db.Column(db.Enum(NotificationPriority), nullable=False,
                         default=NotificationPriority.NORMAL.name)
    title = db.Column(db.String, nullable=False)
    message = db.Column(db.Text)
    # pointers to the real entity (notifications are never the source of truth)
    entity_type = db.Column(db.Enum(NotificationEntityType), nullable=True)
    entity_id = db.Column(db.String, nullable=True)
    action_url = db.Column(db.String, nullable=True)
    actor_user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'), nullable=True)
    pet_id = db.Column(db.String, db.ForeignKey('pets.id'), nullable=True)
    # display-only metadata
    payload = db.Column(JSONB, nullable=True)
    # prevents duplicates (used by idempotent cron generation)
    dedupe_key = db.Column(db.String, nullable=True, unique=True, index=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    dismissed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        def dt(v):
            return v.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if v else None
        return {
            "id": self.id,
            "created_at": dt(self.created_at),
            "updated_at": dt(self.updated_at),
            "user_id": self.user_id,
            "type": self.type.name if self.type else None,
            "status": self.status.name if self.status else NotificationStatus.UNREAD.name,
            "priority": self.priority.name if self.priority else NotificationPriority.NORMAL.name,
            "title": self.title,
            "message": self.message,
            "entity_type": self.entity_type.name if self.entity_type else None,
            "entity_id": self.entity_id,
            "action_url": self.action_url,
            "actor_user_id": self.actor_user_id,
            "shelter_id": self.shelter_id,
            "pet_id": self.pet_id,
            "payload": self.payload,
            "dedupe_key": self.dedupe_key,
            "scheduled_at": dt(self.scheduled_at),
            "read_at": dt(self.read_at),
            "dismissed_at": dt(self.dismissed_at),
            "expires_at": dt(self.expires_at),
        }
