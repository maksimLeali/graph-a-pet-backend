from repository import db, Base

class Media(Base):
    __tablename__ = 'medias'
    type = db.Column(db.String)
    scope = db.Column(db.String)
    ref_id = db.Column(db.String)
    url = db.Column(db.String)

    def to_dict(self):
        return {
            "id" : self.id,
            "type": self.type,
            "url": self.url,
            "scope": self.scope,
            "ref_id": self.ref_id,
            "created_at": str(self.created_at)
        }