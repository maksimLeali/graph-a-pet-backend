from enum import Enum
from repository import db, Base


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


class ShelterTask(Base):
    __tablename__ = 'shelter_tasks'

    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'), nullable=False, index=True)
    shelter_pet_id = db.Column(db.String, db.ForeignKey('shelter_pets.id'), nullable=True)
    # FK verso shelter_boxes aggiunta in fase 3 (tabella non ancora esistente)
    shelter_box_id = db.Column(db.String, nullable=True)
    task_type = db.Column(db.Enum(ShelterTaskType), nullable=False)
    area = db.Column(db.String(120))
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.PENDING.name)
    assigned_to_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed_by_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_rule = db.Column(db.String(120))
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
            "assigned_to_id": self.assigned_to_id,
            "scheduled_at": dt(self.scheduled_at),
            "completed_at": dt(self.completed_at),
            "completed_by_id": self.completed_by_id,
            "is_recurring": bool(self.is_recurring),
            "recurrence_rule": self.recurrence_rule,
            "template_id": self.template_id,
            "notes": self.notes,
        }
