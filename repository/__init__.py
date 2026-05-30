from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from api import app
from config import cfg 
from sqlalchemy.engine import reflection
import json
from decimal import Decimal
from sqlalchemy.ext.declarative import declarative_base


uri = f"postgresql://{cfg['db']['user']}:{cfg['db']['password']}@{cfg['db']['host']}:{cfg['db']['port']}/{cfg['db']['table']}"
schema = cfg['db']['schema'] if 'schema' in cfg['db'] else "" 
app.config["SQLALCHEMY_DATABASE_URI"] =uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER']='temp'
metadata = MetaData(schema=schema)
db = SQLAlchemy(app, metadata= metadata)
inspector = reflection.Inspector.from_engine(db.get_engine())

class Base(db.Model):
    __abstract__= True
    __table_args__ = {'schema': schema}
    id = db.Column(db.String, primary_key=True)
    created_at = db.Column(db.DateTime, default= datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
    updated_at = db.Column(db.DateTime)
    
ViewBase = declarative_base()