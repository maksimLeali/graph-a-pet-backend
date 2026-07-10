from enum import Enum
from repository import db, Base, schema


class ShelterTaskType(Enum):
    CLEANING = "CLEANING"
    DEEP_CLEANING = "DEEP_CLEANING"
    FEEDING = "FEEDING"
    MEDICATION = "MEDICATION"
    GROOMING = "GROOMING"
    OTHER = "OTHER"


class TaskStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class ShelterTask(Base):
    __tablename__ = 'shelter_tasks'
    __table_args__ = (
        # One materialized instance per template per scheduled day. Rows with a
        # NULL template_id (one-off tasks) are exempt: Postgres treats NULLs as
        # distinct, so this only constrains recurring instances.
        db.UniqueConstraint('template_id', 'scheduled_date',
                            name='ux_shelter_task_template_scheduled_date'),
        {'schema': schema},
    )

    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'), nullable=False, index=True)
    shelter_pet_id = db.Column(db.String, db.ForeignKey('shelter_pets.id'), nullable=True)
    # FK verso shelter_boxes aggiunta in fase 3 (tabella non ancora esistente)
    shelter_box_id = db.Column(db.String, nullable=True)
    task_type = db.Column(db.Enum(ShelterTaskType), nullable=False)
    area = db.Column(db.String(120))
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.PENDING.name)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    # calendar day the instance is scheduled for; anchors cron idempotency
    scheduled_date = db.Column(db.Date, nullable=True, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed_by_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    skipped_at = db.Column(db.DateTime, nullable=True)
    skipped_by_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    # --- ricorrenza (template con is_recurring=True) ---
    recurrence_freq = db.Column(db.String(10))          # DAILY | WEEKLY | MONTHLY
    recurrence_interval = db.Column(db.Integer, default=1)  # ogni N
    recurrence_weekdays = db.Column(db.ARRAY(db.String))    # WEEKLY: giorni; MONTHLY: giorno target
    recurrence_week_ordinal = db.Column(db.Integer)        # MONTHLY: 1..5 = primo..quinto, -1 = ultimo
    recurrence_time = db.Column(db.String(5))             # "HH:MM"
    recurrence_start = db.Column(db.DateTime)             # data inizio ricorrenza
    # se materializzata da un template ricorrente, punta al task template
    template_id = db.Column(db.String, db.ForeignKey('shelter_tasks.id', ondelete='SET NULL'), nullable=True)
    notes = db.Column(db.Text)

    def to_dict(self):
        def dt(v):
            return v.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if v else None
        return {
            "id": self.id,
            "created_at": dt(self.created_at),
            "updated_at": dt(self.updated_at),
            "shelter_id": self.shelter_id,
            "shelter_pet_id": self.shelter_pet_id,
            "shelter_box_id": self.shelter_box_id,
            "task_type": self.task_type.name if self.task_type else None,
            "area": self.area,
            "status": self.status.name if self.status else TaskStatus.PENDING.name,
            "scheduled_at": dt(self.scheduled_at),
            "scheduled_date": self.scheduled_date.strftime('%Y-%m-%d') if self.scheduled_date else None,
            "completed_at": dt(self.completed_at),
            "completed_by_id": self.completed_by_id,
            "skipped_at": dt(self.skipped_at),
            "skipped_by_id": self.skipped_by_id,
            "is_recurring": bool(self.is_recurring),
            "recurrence_freq": self.recurrence_freq,
            "recurrence_interval": self.recurrence_interval,
            "recurrence_weekdays": list(self.recurrence_weekdays) if self.recurrence_weekdays else None,
            "recurrence_week_ordinal": self.recurrence_week_ordinal,
            "recurrence_time": self.recurrence_time,
            "recurrence_start": dt(self.recurrence_start),
            "template_id": self.template_id,
            "notes": self.notes,
        }


class ShelterTaskAssignee(Base):
    __tablename__ = 'shelter_task_assignees'
    __table_args__ = (
        # exactly one of user_id / shelter_person_id is set (enforced in domain
        # layer): user_id for an app user, shelter_person_id for a shelter
        # contact/volunteer without an account.
        db.UniqueConstraint('task_id', 'user_id', name='ux_shelter_task_assignee'),
        db.UniqueConstraint('task_id', 'shelter_person_id', name='ux_shelter_task_assignee_shelter_person'),
        {'schema': schema},
    )

    task_id = db.Column(db.String, db.ForeignKey('shelter_tasks.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True, index=True)
    shelter_person_id = db.Column(db.String, db.ForeignKey('shelter_people.id'), nullable=True, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "shelter_person_id": self.shelter_person_id,
        }
