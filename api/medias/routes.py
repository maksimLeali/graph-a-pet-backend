from flask import Blueprint, request, jsonify, abort, send_file
from libs.logger import logger, stringify
import domain.medias as mediaDomain
from api.blueprints import media


@media.route('/<id>/', methods=["GET"])
def get_media_no_size(id):
    logger.api(f"id: {id}")
    return {"data" : { "id": id}}

@media.route('/<id>/fit/<size>', methods=["GET"])
def get_resized_fit_media(id,size):
    try:
        logger.api(f"id: {id}, size: {stringify(size)}")
        # media, media_type = mediaDomain.get_resized_media(id, {"width": int(size.split("x")[0]) , "height": int(size.split("x")[1]) })
        # logger.check(f"type: {media_type}")
        # logger.check(f"{type(media)}")
        return {"media": "fit"}
    except Exception as e: 
        logger.error(e)
        return abort(400, 'unable to process')

@media.route('/<id>/<size>', methods=["GET"])
def get_resized_media(id,size):
    try:
        logger.api(f"id: {id}, size: {stringify(size)}")
        media, media_type = mediaDomain.get_resized_media(id, {"width": int(size.split("x")[0]) , "height": int(size.split("x")[1]) })
        logger.check(f"type: {media_type}")
        logger.check(f"{type(media)}")
        return send_file(media, media_type)
    except Exception as e: 
        logger.error(e)
        return abort(400, 'unable to process')
    
    
    
    
@media.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
            return abort(400, 'No file part')
    file = request.files['file']
    if not file or file.filename == '':
        return abort(400, 'no file selected')
    try:
        public_url, type, encoding, size = mediaDomain.upload_media(file)
        return jsonify({"public_url" : public_url, "type": type, "size": size, "encodig": encoding}), 200
    except Exception as e:
        logger.error(e)