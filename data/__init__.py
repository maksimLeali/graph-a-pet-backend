from api import app
from flask_sqlalchemy import SQLAlchemy
from config import cfg 
import os 

print(os.getenv('DATABASE_URL', "postgresql://"))
print("################")
print(f"postgresql://{cfg['db']['user']}:{cfg['db']['password']}@{cfg['db']['host']}:{cfg['db']['port']}/{cfg['db']['table']}")
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{cfg['db']['user']}:{cfg['db']['password']}@{cfg['db']['host']}:{cfg['db']['port']}/{cfg['db']['table']}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

