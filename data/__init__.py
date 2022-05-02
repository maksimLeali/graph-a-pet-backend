from api import app
from flask_sqlalchemy import SQLAlchemy
import yaml

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{cfg['db']['user']}:{cfg['db']['password']}@{cfg['db']['host']}:{cfg['db']['port']}/{cfg['db']['table']}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

