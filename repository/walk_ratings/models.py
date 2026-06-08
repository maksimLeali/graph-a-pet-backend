from enum import Enum
from repository import db, Base


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
            "created_at": str(self.created_at),
            "walk_id": self.walk_id,
            "type": self.type.name if self.type else None,
            "rating": self.rating,
        }
