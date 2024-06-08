from flask import Blueprint

media = Blueprint('media', __name__, url_prefix='/media')
translations = Blueprint('translations', __name__, url_prefix='/translations')