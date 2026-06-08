from repository import db, Base


class Walk(Base):
    __tablename__ = 'walks'    
    distance_km = db.Column(db.Float, nullable=False)    
    treatment_id= db.Column(db.String, db.ForeignKey('treatments.id'))

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": str(self.created_at),
            "distance_km": self.distance_km,
            "treatment_id": self.treatment_id,
        }