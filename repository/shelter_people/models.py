from enum import Enum
from repository import db, Base


class ShelterPersonStatus(Enum):
    VISITOR = "VISITOR"
    VOLUNTEER = "VOLUNTEER"
    PENDING_INVITE = "PENDING_INVITE"
    ACTIVE_USER = "ACTIVE_USER"
    ARCHIVED = "ARCHIVED"


class ShelterPersonSource(Enum):
    MANUAL = "MANUAL"
    INVITE = "INVITE"
    VISIT = "VISIT"
    VOLUNTEER_REQUEST = "VOLUNTEER_REQUEST"
    IMPORT = "IMPORT"


class ShelterPerson(Base):
    __tablename__ = 'shelter_people'

    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'), nullable=False, index=True)
    # optional link to a real app account; NULL for people without one
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True, index=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String, nullable=True)
    phone = db.Column(db.String, nullable=True)
    status = db.Column(db.Enum(ShelterPersonStatus), nullable=False,
                       default=ShelterPersonStatus.VISITOR.name, index=True)
    source = db.Column(db.Enum(ShelterPersonSource), nullable=False,
                       default=ShelterPersonSource.MANUAL.name)
    notes = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    archived_at = db.Column(db.DateTime, nullable=True)
    archived_by_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        def dt(v):
            return v.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if v else None
        return {
            "id": self.id,
            "created_at": dt(self.created_at),
            "updated_at": dt(self.updated_at),
            "shelter_id": self.shelter_id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status.name if self.status else ShelterPersonStatus.VISITOR.name,
            "source": self.source.name if self.source else ShelterPersonSource.MANUAL.name,
            "notes": self.notes,
            "created_by_id": self.created_by_id,
            "archived_at": dt(self.archived_at),
            "archived_by_id": self.archived_by_id,
        }
