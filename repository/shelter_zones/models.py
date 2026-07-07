from repository import db, Base


class ShelterZone(Base):
    __tablename__ = 'shelter_zones'

    map_id = db.Column(db.String, db.ForeignKey('shelter_maps.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(120))
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
            "x": fl(self.x),
            "y": fl(self.y),
            "width": fl(self.width),
            "height": fl(self.height),
            "color": self.color,
        }
