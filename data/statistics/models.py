from enum import Enum
from data import db
from datetime import datetime

class Statistic(db.Model): 
    __tablename__ = 'statistics'
    id = db.Column(db.String, primary_key=True)
    date = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ') )
    deleted_at = db.Column(db.DateTime)
    active_users = db.Column(db.Integer)
    all_users = db.Column(db.Integer)
    all_pets = db.Column(db.Integer)
    def to_dict(self):
        return {
            "id": self.id,
            "date": str(self.date),
            "active_users": self.active_users, 
            "all_pets": self.all_pets,
            "all_users": self.all_users
        }