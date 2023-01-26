from api.errors import BadRequest
from libs.logger import logger
from libs.firebase.storage import upload_image
import os
# from config import cfg

from werkzeug.utils import secure_filename
from libs.utils import allowed_files

def upload_media(file):
    try: 
        logger.domain('try to upload media')
        if file and allowed_files(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join('temp', filename))
            return upload_image('temp'+'/', filename)
        error = BadRequest(f"file not allowed")
        raise error
    except Exception as e: 
        logger.error(e)
        raise e