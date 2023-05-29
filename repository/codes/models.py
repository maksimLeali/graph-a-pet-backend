from repository import db, Base

class Code(Base):
    __tablename__ = 'codes'
    code = db.Column(db.String)
    ref_id = db.Column(db.String)
    ref_table= db.Column(db.String)
    created_by= db.Column(db.String, db.ForeignKey('users.id'))

    def to_dict(self):
        return {
            "id" : self.id,
            "code": self.code,
            "ref_id": self.ref_id,
            "ref_table": self.ref_table,
            "created_at": str(self.created_at),
            "created_by": self.created_by,
        }