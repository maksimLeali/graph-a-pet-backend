from flask import Blueprint, request, jsonify, abort
from libs.logger import logger
import domain.medias.rest_method as mediaRestDomain
from api.blueprints import media


@media.route('/', methods=["GET"])
def get_media():
    return {"res" :"Welcome to the media API"}

@media.route('/<id>/', methods=["GET"])
def get_resized_media(id,size):
    logger.api(f"id: {id}")
    return {"data" : { "id": id}}

@media.route('/<id>/<size>', methods=["GET"])
def get_media_no_size(id,size):
    width= size.split('x')[0]
    height= size.split('x')[1]
    logger.api(f"id: {id}, width: {width}, height: {height}")
    return {"data" : { "id": id}}

@media.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
            return abort(400, 'No file part')
    file = request.files['file']
    if not file or file.filename == '':
        return abort(400, 'no file selected')
    try:
        public_url, type, encoding, size = mediaRestDomain.upload_media(file)
        return jsonify({"public_url" : public_url, "type": type, "size": size, "encodig": encoding}), 200
    except Exception as e:
        logger.error(e)