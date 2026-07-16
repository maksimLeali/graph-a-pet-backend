from enum import Enum
from repository import db
from datetime import datetime
from config import cfg 
from utils.dates import utc_now, iso_z
class Statistic(db.Model): 
    __tablename__ = 'statistics'
    __table_args__ = {'schema': cfg['db']['schema'] if 'schema' in cfg['db'] else None}
    id = db.Column(db.String, primary_key=True)
    date = db.Column(db.DateTime, default=utc_now)
    active_users = db.Column(db.Integer)
    all_users = db.Column(db.Integer)
    all_pets = db.Column(db.Integer)
    def to_dict(self):
        return {
            "id": self.id,
            "date": iso_z(self.date),
            "active_users": self.active_users, 
            "all_pets": self.all_pets,
            "all_users": self.all_users
        }