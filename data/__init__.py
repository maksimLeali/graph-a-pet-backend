from api import app
from os import getenv
from flask_sqlalchemy import SQLAlchemy
from config import cfg 

app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL", "sqlite://")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

