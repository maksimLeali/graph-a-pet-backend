from data import db
from data.models import *

class Pet(db.Model):
    __tablename__ = 'pets'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    race = db.Column(db.String)
    ownerships = db.relationship("Ownership", uselist=True, backref='pets')
    created_at = db.Column(db.Date)
    def to_dict(self):
        return {
            "id": self.id,
            "race": self.race,
            "name": self.name,
            "created_at": str(self.created_at.strftime('%d-%m-%Y'))
        }
