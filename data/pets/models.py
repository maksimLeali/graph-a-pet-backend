from data import db
from data.models import *
from datetime import datetime
class Pet(db.Model):
    __tablename__ = 'pets'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    race = db.Column(db.String)
    ownerships = db.relationship("Ownership", uselist=True, backref='pets')
    birthday= db.Column(db.Date)
    neutered= db.Column(db.Boolean, default= False)
    coat_id= db.Column(db.String, db.ForeignKey('coats.id'))
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    def to_dict(self):
        return {
            "id": self.id,
            "race": self.race,
            "name": self.name,
            "birthday": self.birthday,
            "neutered": self.neutered,
            "coat_id": self.coat_id,
            "created_at": str(self.created_at)
        }
