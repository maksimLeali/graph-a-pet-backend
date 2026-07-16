from repository import db, Base
from repository.walk_ratings.models import WalkRatingType
from utils.dates import iso_z


class ShelterWalkRating(Base):
    __tablename__ = 'shelter_walk_ratings'
    walk_id = db.Column(db.String, db.ForeignKey('shelter_walks.id'), nullable=False, index=True)
    type = db.Column(db.Enum(WalkRatingType))
    rating = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": iso_z(self.created_at),
            "walk_id": self.walk_id,
            "type": self.type.name if self.type else None,
            "rating": self.rating,
        }
