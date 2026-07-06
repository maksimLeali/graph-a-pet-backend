from enum import Enum
from repository import db, Base


class MapElementType(Enum):
    WALL = "WALL"
    DOOR = "DOOR"
    GATE = "GATE"
    WATER_POINT = "WATER_POINT"
    FEEDING_POINT = "FEEDING_POINT"
    BENCH = "BENCH"
    TREE = "TREE"
    OTHER = "OTHER"


class ShelterMapElement(Base):
    __tablename__ = 'shelter_map_elements'

    map_id = db.Column(db.String, db.ForeignKey('shelter_maps.id', ondelete='CASCADE'), nullable=False, index=True)
    element_type = db.Column(db.Enum(MapElementType), nullable=False)
    x = db.Column(db.Numeric(10, 2))
    y = db.Column(db.Numeric(10, 2))
    width = db.Column(db.Numeric(10, 2))
    height = db.Column(db.Numeric(10, 2))
    rotation = db.Column(db.Numeric(6, 2), default=0)
    color = db.Column(db.String(20))
    label = db.Column(db.String(120))

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
            "element_type": self.element_type.name if self.element_type else None,
            "x": fl(self.x),
            "y": fl(self.y),
            "width": fl(self.width),
            "height": fl(self.height),
            "rotation": fl(self.rotation) if self.rotation is not None else 0.0,
            "color": self.color,
            "label": self.label,
        }
