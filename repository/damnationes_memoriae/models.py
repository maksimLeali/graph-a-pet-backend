from repository import db

from datetime import datetime


class DamnationesMemoriae(db.Model):
    id = db.Column(db.String, primary_key=True)
    original_table =  db.Column(db.String)
    created_at =  db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    original_data = db.Column(db.JSON)
    deleted_by = db.Column(db.String)
    restore_before  = db.Column(db.ARRAY(db.String))
    restore_after  = db.Column(db.ARRAY(db.String))
    def to_dict(self) :
        return  {
            "id":  self.id,
            "created_at":  str(self.created_at),
            "original_table": self.original_table,
            "original_data":  self.original_data,
            "restore_before": self.restore_before,
            "restore_after": self.restore_after,
            "deleted_by": self.deleted_by
        }