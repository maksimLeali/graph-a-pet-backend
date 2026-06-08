from repository import db, Base


class ShelterPet(Base):
    __tablename__ = 'shelter_pets'
    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'))
    pet_id = db.Column(db.String, db.ForeignKey('pets.id'))

    def to_dict(self):
        return {
            "id": self.id,
            "shelter_id": self.shelter_id,
            "pet_id": self.pet_id,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }
