import os
import uuid
import mimetypes
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.logger import logger
from utils.dates import utc_now

MEDIA_ROOT = 'media'


def save_image(file, user_id):
    safe_user = secure_filename(str(user_id)) or 'anonymous'
    date_dir = utc_now().strftime('%Y-%m-%d')
    rel_dir = os.path.join(MEDIA_ROOT, safe_user, date_dir)
    os.makedirs(rel_dir, exist_ok=True)

    safe_name = secure_filename(file.filename) or 'file'
    final_name = f"{uuid.uuid4().hex}_{safe_name}"
    rel_path = os.path.join(rel_dir, final_name).replace('\\', '/')

    file.save(rel_path)

    mime, encoding = mimetypes.guess_type(rel_path)
    size = os.path.getsize(rel_path)
    logger.info(f"saved media to {rel_path} ({mime}, {size} bytes)")
    return rel_path, mime, encoding, size
