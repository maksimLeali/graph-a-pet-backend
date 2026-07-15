from repository import db, Base


class ShelterPet(Base):
    __tablename__ = 'shelter_pets'
    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'))
    pet_id = db.Column(db.String, db.ForeignKey('pets.id'))
    # a transfer deactivates the source membership instead of mutating it,
    # so a pet has exactly one active ShelterPet at any time
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default='true')
    left_at = db.Column(db.DateTime, nullable=True)
    # gates public storefront/donation visibility — separate from is_active
    # (a pet can belong to a public shelter without being published for
    # donations yet)
    is_published = db.Column(db.Boolean, nullable=False, default=False, server_default='false')

    def to_dict(self):
        return {
            "id": self.id,
            "shelter_id": self.shelter_id,
            "pet_id": self.pet_id,
            "is_active": bool(self.is_active) if self.is_active is not None else True,
            "left_at": self.left_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if self.left_at else None,
            "is_published": bool(self.is_published) if self.is_published is not None else False,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }
