from flask import Flask, Blueprint
from flask_cors import CORS

app = Flask(__name__)

CORS(app)