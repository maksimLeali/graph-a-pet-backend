from enum import Enum
from repository import db, Base


class ShelterWalkStatus(Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ShelterWalk(Base):
    __tablename__ = 'shelter_walks'

    shelter_pet_id = db.Column(db.String, db.ForeignKey('shelter_pets.id'), nullable=False, index=True)
    walker_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Enum(ShelterWalkStatus), default=ShelterWalkStatus.PLANNED.name)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text)

    def to_dict(self):
        def dt(v):
            return v.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if v else None
        return {
            "id": self.id,
            "created_at": dt(self.created_at),
            "updated_at": dt(self.updated_at),
            "shelter_pet_id": self.shelter_pet_id,
            "walker_id": self.walker_id,
            "status": self.status.name if self.status else ShelterWalkStatus.PLANNED.name,
            "scheduled_at": dt(self.scheduled_at),
            "started_at": dt(self.started_at),
            "ended_at": dt(self.ended_at),
            "duration_minutes": self.duration_minutes,
            "notes": self.notes,
        }
