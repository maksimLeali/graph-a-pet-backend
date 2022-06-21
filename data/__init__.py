from api import app
import os
from flask_sqlalchemy import SQLAlchemy
from config import cfg 

print(os.getenv("DATABASE_URL", "sqlite://"))

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "postgresql://")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

