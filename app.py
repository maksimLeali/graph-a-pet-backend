from api import app
from ariadne import graphql_sync, load_schema_from_path, make_executable_schema, \
    snake_case_fallback_resolvers
from ariadne.constants import PLAYGROUND_HTML
from flask import request, jsonify
from api.operations import object_types
from config import cfg
from libs.logger import logger
import os

type_defs = load_schema_from_path("./")
schema = make_executable_schema(
    type_defs, object_types,  snake_case_fallback_resolvers
)

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

os.environ['WERKZEUG_RUN_MAIN'] = 'true'
if __name__ == "__main__":
    logger.start(
        f"Server is running on http://{cfg['flask']['host']}:{cfg['flask']['port']}\n" \
        f"See playground on http://{cfg['flask']['host']}:{cfg['flask']['port']}/graphql"
        )
    app.run(host=cfg['flask']['host'], port=cfg['flask']['port'])