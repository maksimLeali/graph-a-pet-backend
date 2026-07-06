from datetime import datetime
from repository import db, Base


class ShelterBoxOccupancy(Base):
    __tablename__ = 'shelter_box_occupancies'

    box_id = db.Column(db.String, db.ForeignKey('shelter_boxes.id'), nullable=False, index=True)
    shelter_pet_id = db.Column(db.String, db.ForeignKey('shelter_pets.id'), nullable=False, index=True)
    entered_at = db.Column(db.DateTime, nullable=False)
    exited_at = db.Column(db.DateTime, nullable=True)
    moved_by_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    reason = db.Column(db.String(200))

    def to_dict(self):
        def dt(v):
            return v.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if v else None
        return {
            "id": self.id,
            "created_at": dt(self.created_at),
            "updated_at": dt(self.updated_at),
            "box_id": self.box_id,
            "shelter_pet_id": self.shelter_pet_id,
            "entered_at": dt(self.entered_at),
            "exited_at": dt(self.exited_at),
            "moved_by_id": self.moved_by_id,
            "reason": self.reason,
        }
