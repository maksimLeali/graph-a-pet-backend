from data import db
from data.models import *
from datetime import datetime

class Media(db.Model):
    __tablename__ = 'medias'
    id = db.Column(db.String, primary_key=True)
    type = db.Column(db.String)
    scope = db.Column(db.String)
    ref_id = db.Column(db.String)
    url = db.Column(db.String)
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    def to_dict(self):
        return {
            "id" : self.id,
            "type": self.type,
            "url": self.type,
            "scope": self.scope,
            "refId": self.ref_id,
            "created_at": str(self.created_at)
        }