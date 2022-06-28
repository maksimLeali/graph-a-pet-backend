from flask import Flask
from flask_cors import CORS
import logging

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True
CORS(app)