from repository import db, Base, schema


class ShelterBox(Base):
    __tablename__ = 'shelter_boxes'
    __table_args__ = (
        db.UniqueConstraint('map_id', 'label', name='ux_shelter_box_map_label'),
        db.CheckConstraint('capacity > 0', name='ck_shelter_box_capacity_positive'),
        {'schema': schema},
    )

    map_id = db.Column(db.String, db.ForeignKey('shelter_maps.id', ondelete='CASCADE'), nullable=False, index=True)
    zone_id = db.Column(db.String, db.ForeignKey('shelter_zones.id', ondelete='CASCADE'), nullable=False, index=True)
    area_id = db.Column(db.String, db.ForeignKey('shelter_areas.id', ondelete='SET NULL'), nullable=True)
    label = db.Column(db.String(60), nullable=False)
    x = db.Column(db.Numeric(10, 2))
    y = db.Column(db.Numeric(10, 2))
    width = db.Column(db.Numeric(10, 2))
    height = db.Column(db.Numeric(10, 2))
    rotation = db.Column(db.Numeric(6, 2), default=0)
    capacity = db.Column(db.Integer, default=1)
    is_out_of_service = db.Column(db.Boolean, default=False)
    last_cleaned_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)

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
            "zone_id": self.zone_id,
            "area_id": self.area_id,
            "label": self.label,
            "x": fl(self.x),
            "y": fl(self.y),
            "width": fl(self.width),
            "height": fl(self.height),
            "rotation": fl(self.rotation) if self.rotation is not None else 0.0,
            "capacity": self.capacity if self.capacity is not None else 1,
            "is_out_of_service": bool(self.is_out_of_service),
            "last_cleaned_at": dt(self.last_cleaned_at),
            "notes": self.notes,
        }
