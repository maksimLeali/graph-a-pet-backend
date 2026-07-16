from enum import Enum
from repository import db, Base
from utils.dates import iso_z


class WalkRatingType(Enum):
    OVERALL = "OVERALL",
    LEASH_PULLING = "LEASH_PULLING",
    BEHAVIOR = "BEHAVIOR",
    AGGRESSION = "AGGRESSION",
    CALM = "CALM"


class WalkRating(Base):
    __tablename__ = 'walk_ratings'
    walk_id = db.Column(db.String, db.ForeignKey('walks.id'))
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
