from repository import db, Base
from utils.dates import iso_z

class Code(Base):
    __tablename__ = 'codes'
    code = db.Column(db.String)
    ref_id = db.Column(db.String)
    ref_table= db.Column(db.String)    
    scope= db.Column(db.String)
    valid= db.Column(db.Boolean, default=True )
    def to_dict(self):
        return {
            "id" : self.id,
            "code": self.code,
            "ref_id": self.ref_id,
            "ref_table": self.ref_table,
            "scope": self.scope,
            "valid": self.valid,
            "created_at": iso_z(self.created_at)
        }