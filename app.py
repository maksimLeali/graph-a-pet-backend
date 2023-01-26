from pendulum import SECONDS_PER_MINUTE
from api import app
from libs.logger import logger
import os
import logging
from ariadne import graphql_sync, load_schema_from_path, make_executable_schema, \
    snake_case_fallback_resolvers
from ariadne.constants import PLAYGROUND_HTML
from flask import Blueprint, request, jsonify, abort
from api.operations import object_types
from config import cfg
from libs.firebase.storage import upload_image
from libs.cron import start_scheduler
import schedules
from api.medias.routes import *
from api.blueprints import media

type_defs = load_schema_from_path("./")
schema = make_executable_schema(
    type_defs, object_types,  snake_case_fallback_resolvers
)

if (cfg['cron']['active']):
    start_scheduler()
else :
    logger.setup('cron disabled')


@app.route("/graphql", methods=["GET"])
def graphql_playground():
    return PLAYGROUND_HTML, 200

@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    success, result =graphql_sync(
        schema,
        data,
        context_value=request,
        debug=app.debug,
        logger="graph_a_pet"
    )
    status_code = 200 if success else 400
    return jsonify(result), status_code
    

if __name__ == "__main__":
    log = logging.getLogger('werkzeug')
    log.disabled = True
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    app.register_blueprint(media)
    logger.start(
        f"Server is running on http://{cfg['flask']['host']}:{cfg['flask']['port']}\n" \
        f"See playground on http://{cfg['flask']['host']}:{cfg['flask']['port']}/graphql\n"
        )
    app.run(host=cfg['flask']['host'], port=cfg['flask']['port'], debug=False)