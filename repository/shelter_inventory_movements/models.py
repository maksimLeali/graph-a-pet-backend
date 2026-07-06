from enum import Enum
from repository import db, Base


class MovementType(Enum):
    RESTOCK = "RESTOCK"
    CONSUMPTION = "CONSUMPTION"
    DONATION = "DONATION"
    WASTE = "WASTE"
    ADJUSTMENT = "ADJUSTMENT"


class ShelterInventoryMovement(Base):
    __tablename__ = 'shelter_inventory_movements'

    item_id = db.Column(db.String, db.ForeignKey('shelter_inventory_items.id'), nullable=False, index=True)
    movement_type = db.Column(db.Enum(MovementType), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    registered_by_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
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
            "item_id": self.item_id,
            "movement_type": self.movement_type.name if self.movement_type else None,
            "quantity": fl(self.quantity),
            "registered_by_id": self.registered_by_id,
            "notes": self.notes,
        }
