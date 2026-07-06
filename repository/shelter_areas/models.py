from enum import Enum
from repository import db, Base


class AreaType(Enum):
    KENNEL = "KENNEL"
    QUARANTINE = "QUARANTINE"
    PLAYGROUND = "PLAYGROUND"
    MEDICAL = "MEDICAL"
    STORAGE = "STORAGE"
    OFFICE = "OFFICE"
    COMMON = "COMMON"
    OUTDOOR = "OUTDOOR"
    OTHER = "OTHER"


class ShelterArea(Base):
    __tablename__ = 'shelter_areas'

    map_id = db.Column(db.String, db.ForeignKey('shelter_maps.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(120))
    area_type = db.Column(db.Enum(AreaType))
    x = db.Column(db.Numeric(10, 2))
    y = db.Column(db.Numeric(10, 2))
    width = db.Column(db.Numeric(10, 2))
    height = db.Column(db.Numeric(10, 2))
    color = db.Column(db.String(20))

    def to_dict(self):
        def dt(v):
            return v.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if v else None
        def fl(v):
            return float(v) if v is not None else None
        return {
            "id": self.id,
            "created_at": dt(self.created_at),
            "updated_at": dt(self.updated_at),
            "map_id": self.map_id,
            "name": self.name,
            "area_type": self.area_type.name if self.area_type else None,
            "x": fl(self.x),
            "y": fl(self.y),
            "width": fl(self.width),
            "height": fl(self.height),
            "color": self.color,
        }
