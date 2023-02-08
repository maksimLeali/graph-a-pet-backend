from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from controller import app
from config import cfg 
from sqlalchemy.engine import reflection

app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{cfg['db']['user']}:{cfg['db']['password']}@{cfg['db']['host']}:{cfg['db']['port']}/{cfg['db']['table']}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER']='temp'
db = SQLAlchemy(app)
inspector = reflection.Inspector.from_engine(db.get_engine())

class Base(db.Model):
    __abstract__= True
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    updated_at = db.Column(db.DateTime)
    