from repository import db, Base

# Elenco delle metriche KPI storicizzate (una riga per shelter per giorno).
KPI_FIELDS = [
    "walks_completed_today",
    "walks_planned_today",
    "pets_needing_walk",
    "tasks_pending",
    "tasks_overdue",
    "tasks_completed_today",
    "tasks_total",
    "tasks_recurring",
    "tasks_due_this_week",
    "boxes_total",
    "boxes_free",
    "boxes_occupied",
    "boxes_full",
    "boxes_out_of_service",
    "pets_total",
    "pets_without_box",
    "low_stock_count",
]


class ShelterKpiSnapshot(Base):
    __tablename__ = 'shelter_kpi_snapshots'
    __table_args__ = (
        db.UniqueConstraint('shelter_id', 'snapshot_date', name='uq_shelter_kpi_day'),
    )

    shelter_id = db.Column(db.String, db.ForeignKey('shelters.id', ondelete='CASCADE'), nullable=False, index=True)
    snapshot_date = db.Column(db.Date, nullable=False, index=True)

    walks_completed_today = db.Column(db.Integer, default=0)
    walks_planned_today = db.Column(db.Integer, default=0)
    pets_needing_walk = db.Column(db.Integer, default=0)
    tasks_pending = db.Column(db.Integer, default=0)
    tasks_overdue = db.Column(db.Integer, default=0)
    tasks_completed_today = db.Column(db.Integer, default=0)
    tasks_total = db.Column(db.Integer, default=0)
    tasks_recurring = db.Column(db.Integer, default=0)
    tasks_due_this_week = db.Column(db.Integer, default=0)
    boxes_total = db.Column(db.Integer, default=0)
    boxes_free = db.Column(db.Integer, default=0)
    boxes_occupied = db.Column(db.Integer, default=0)
    boxes_full = db.Column(db.Integer, default=0)
    boxes_out_of_service = db.Column(db.Integer, default=0)
    pets_total = db.Column(db.Integer, default=0)
    pets_without_box = db.Column(db.Integer, default=0)
    low_stock_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        d = {
            "id": self.id,
            "shelter_id": self.shelter_id,
            "date": self.snapshot_date.isoformat() if self.snapshot_date else None,
        }
        for f in KPI_FIELDS:
            d[f] = getattr(self, f) or 0
        return d
