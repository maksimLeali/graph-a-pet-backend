from api import app
from flask_sqlalchemy import SQLAlchemy


app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres@localhost:5432/test"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

