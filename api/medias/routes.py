from flask import request, jsonify, abort, send_file
from utils.logger import logger, stringify
import domain.medias as mediaDomain
from api.blueprints import media
from api.errors import format_error
from utils import get_request_user


@media.route('/<id>/', methods=["GET"])
def get_media_no_size(id):
    logger.api(f"id: {id}")
    try: 
        media,media_type = mediaDomain.get_media_file(id,request.args)
        logger.check(f"type: {media_type}")
        return send_file(path_or_file=media, mimetype=media_type, max_age=3600)
    except Exception as e:
        logger.error(e)
        formatted_error = format_error(e)
        logger.info(formatted_error)
        return abort(formatted_error.get("code"), formatted_error.get("message"))
    
@media.route('/<id>/<size>/fit', methods=["GET"])
def get_resized_fit_media(id,size):
    logger.api(f"id: {id}, size: {stringify(size)}")
    try:
        media, media_type = mediaDomain.get_resized_to_fit_media(id, {"width": int(size.split("x")[0]) , "height": int(size.split("x")[1]) }, request.args)
        logger.check(f"type: {media_type}")
        return send_file(path_or_file=media, mimetype=media_type, max_age=3600)
    except Exception as e: 
        logger.error(e)
        formatted_error = format_error(e)
        logger.info(formatted_error)
        return abort(formatted_error.get("code"), formatted_error.get("message"))

@media.route('/<id>/<size>', methods=["GET"])
def get_resized_media(id,size):
    try:
        logger.critical(f"id: {id}, size: {stringify(size)}")
        logger.api(f"id: {id}, size: {stringify(size)}")
        media, media_type = mediaDomain.get_cropped_media(id, {"width": int(size.split("x")[0]) , "height": int(size.split("x")[1]) }, request.args)
        logger.check(f"type: {media_type}")
        return send_file(path_or_file=media, mimetype=media_type, max_age=3600)
    except Exception as e: 
        logger.error(e)
        formatted_error = format_error(e)
        logger.info(formatted_error)
        return abort(formatted_error.get("code"), formatted_error.get("message"))
    
    
    
    
@media.route('/upload', methods=['POST'])
def upload_file():
    print("here")
    if 'file' not in request.files:
            return abort(400, 'No file part')
    file = request.files['file']
    
    if not file or file.filename == '':
        return abort(400, 'no file selected')
    disable_colors = request.form.get('disable_colors', 'false').lower() == 'true'
    print(disable_colors)

    user_id = 'anonymous'
    token = request.headers.get('Authorization') or request.headers.get('authorization')
    logger.info(f"upload auth header present: {bool(token)}")
    if token:
        try:
            user = get_request_user(token)
            logger.info(f"resolved user from token: {stringify(user)}")
            user_id = str(user.get('id') or 'anonymous')
        except Exception as e:
            logger.warn(f"could not resolve user from token, using 'anonymous': {e}")
    logger.info(f"upload user_id: {user_id}")

    try:
        disk_path, mime, encoding, size, colors = mediaDomain.upload_media(file, disable_colors, user_id)
        main_color = colors[0] if colors else None
        return jsonify({
            "public_url": disk_path,
            "url": disk_path,
            "type": mime,
            "encoding": encoding,
            "size": size,
            "main_colors": colors,
            "main_color": main_color,
        }), 200
    except Exception as e:
        logger.error(e)
        formatted_error = format_error(e)
        return abort(formatted_error.get("code"), formatted_error.get("message"))