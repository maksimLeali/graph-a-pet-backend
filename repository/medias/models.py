from repository import db, Base
from utils.dates import iso_z

class Media(Base):
    __tablename__ = 'medias'
    type = db.Column(db.String)
    scope = db.Column(db.String)
    ref_id = db.Column(db.String)
    main_colors= db.Column(db.JSON, default= [])
    main_color= db.Column(db.JSON)
    url = db.Column(db.String)

    def to_dict(self):
        return {
            "id" : self.id,
            "type": self.type,
            "url": f"/media/{self.id}/",
            "file_path": self.url,
            "scope": self.scope,
            "ref_id": self.ref_id,
            "main_color": self.main_color,
            "main_colors": self.main_colors,
            "created_at": iso_z(self.created_at)
        }