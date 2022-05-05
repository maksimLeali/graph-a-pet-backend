from enum import Enum
from data import db
from data.models import *
from datetime import datetime
    
class CoatLength(Enum) :
    SHORT= "SHORT"
    MEDIUM= "MEDIUM"
    LENGHT= "LENGHT"
    HAIRLESS= "HAIRLESS"

class CoatPattern(Enum) :
    MERLE = "MERLE"
    BRINDLE = "BRINDLE"
    HARLEQUIN = "HARLEQUIN"
    TICKED = "TICKED"
    SPOTTE = "SPOTTE"
    ROAN = "ROAN"
    TRICOLOR = "TRICOLOR"
    BICOLOR = "BICOLOR"
    SOLID = "SOLID"
    COLORPOINT = "COLORPOINT"
    


class Coat(db.Model):
    __tablename__ = 'coats'
    id = db.Column(db.String, primary_key=True)
    colors = db.Column(db.ARRAY(db.String))
    length = db.Column(db.Enum(CoatLength))
    pattern = db.Column(db.Enum(CoatPattern))
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    pet= db.relationship('Pet', backref="coats", lazy=True, uselist=False )
    
    def to_dict(self):
        return {
            "id": self.id,
            "colora": self.colors,
            "pattenr": self.pattern,
            "length": self.length,
            "created_at": str(self.created_at)
        }