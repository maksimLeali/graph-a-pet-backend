from enum import Enum
from repository import db, Base


class InventoryCategory(Enum):
    FOOD_DRY = "FOOD_DRY"
    FOOD_WET = "FOOD_WET"
    MEDICINE = "MEDICINE"
    HYGIENE = "HYGIENE"
    EQUIPMENT = "EQUIPMENT"
    OTHER = "OTHER"


class ShelterInventoryItem(Base):
    __tablename__ = 'shelter_inventory_items'

    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id'), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.Enum(InventoryCategory))
    unit = db.Column(db.String(20))
    minimum_threshold = db.Column(db.Numeric(10, 3))
    # archive flow: items with movement history are archived, never hard-deleted
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default='true')
    archived_at = db.Column(db.DateTime, nullable=True)
    archived_by_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
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
            "shelter_id": self.shelter_id,
            "name": self.name,
            "category": self.category.name if self.category else None,
            "unit": self.unit,
            "minimum_threshold": fl(self.minimum_threshold),
            "is_active": bool(self.is_active) if self.is_active is not None else True,
            "archived_at": dt(self.archived_at),
            "archived_by_id": self.archived_by_id,
            "notes": self.notes,
        }
