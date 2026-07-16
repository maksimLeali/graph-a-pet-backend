from repository import db, Base
from utils.dates import iso_z


class PetWeight(Base):
    __tablename__ = 'pet_weights'
    pet_id = db.Column(db.String, db.ForeignKey('pets.id'), nullable=False, index=True)
    weight_kg = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": iso_z(self.created_at),
            "pet_id": self.pet_id,
            "weight_kg": self.weight_kg,
        }
