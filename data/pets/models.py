from data import db

class Pet(db.Model):
    __tablename__ = 'pets'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    race = db.Column(db.String)
    ownerships = db.relationship("Ownership", uselist=True, backref='pets')
    created_at = db.Column(db.Date)
    ownership_ids = db.Column(db.ARRAY(db.String))
    def to_dict(self):
        return {
            "id": self.id,
            "race": self.race,
            "name": self.name,
            "ownerships": self.ownership_ids,
            "created_at": str(self.created_at.strftime('%d-%m-%Y'))
        }
