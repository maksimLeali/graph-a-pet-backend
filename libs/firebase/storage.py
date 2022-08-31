from firebase_admin import credentials, initialize_app, storage
from config import cfg
from libs.logger import logger




cred = credentials.Certificate("serviceAccountKey.json")
initialize_app(cred, {'storageBucket': cfg['firebase']['bucket']})
def upload_image(dir, file_name):
    logger.info(file_name)
    try:
        # Put your local file path 
        logger.info('here')
        bucket = storage.bucket()
        logger.info('here')
        blob = bucket.blob(file_name)
        logger.info('there')
        blob.upload_from_filename(dir+file_name)
        # Opt : if you want to make public access from the URL
        blob.make_public()
        logger.check(blob.public_url)
        return blob.public_url
    except Exception as e:
        logger.error(e)