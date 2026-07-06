from enum import Enum
from repository import db, Base


class MapUnit(Enum):
    METERS = "METERS"
    PIXELS = "PIXELS"


class ShelterMap(Base):
    __tablename__ = 'shelter_maps'

    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'), nullable=False, index=True)
    name = db.Column(db.String(120))
    width = db.Column(db.Numeric(10, 2))
    height = db.Column(db.Numeric(10, 2))
    unit = db.Column(db.Enum(MapUnit), default=MapUnit.METERS.name)
    background_media_id = db.Column(db.String, db.ForeignKey('medias.id'), nullable=True)

    def to_dict(self):
        def dt(v):
            return v.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if v else None
        def fl(v):
            return float(v) if v is not None else None
        return {
            "id": self.id,
            "created_at": dt(self.created_at),
            "updated_at": dt(self.updated_at),
            "shelter_id": self.shelter_id,
            "name": self.name,
            "width": fl(self.width),
            "height": fl(self.height),
            "unit": self.unit.name if self.unit else MapUnit.METERS.name,
            "background_media_id": self.background_media_id,
        }
