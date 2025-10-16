from repository import db, Base


class Walk(Base):
    __tablename__ = 'walks'    
    distance_km = db.Column(db.Float, nullable=False)    
    treatment_id= db.Column(db.String, db.ForeignKey('treatments.id'))
    overall_rating = db.Column(db.Integer)
    leash_pulling_rating = db.Column(db.Integer)
    behavior_rating = db.Column(db.Integer)
    notes = db.Column(db.ARRAY(db.String))

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": str(self.created_at),
            "distance_km": self.distance_km,
            "treatment_id": self.treatment_id,
            "overall_rating": self.overall_rating,
            "leash_pulling_rating": self.leash_pulling_rating,
            "behavior_rating": self.behavior_rating,
            "notes": self.notes
        }