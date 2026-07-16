from repository import db, Base

from datetime import datetime
from utils.dates import iso_z

class DamnationesMemoriae(Base):
    original_table =  db.Column(db.String)
    original_data = db.Column(db.JSON)
    deleted_by = db.Column(db.String)
    restore_before  = db.Column(db.ARRAY(db.String))
    restore_after  = db.Column(db.ARRAY(db.String))
    def to_dict(self) :
        return  {
            "id":  self.id,
            "created_at":  iso_z(self.created_at),
            "original_table": self.original_table,
            "original_data":  self.original_data,
            "restore_before": self.restore_before,
            "restore_after": self.restore_after,
            "deleted_by": self.deleted_by
        }