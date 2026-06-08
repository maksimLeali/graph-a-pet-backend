SECONDS_PER_MINUTE = 60
from api import app
from utils.logger import logger
import os
import logging
from ariadne import graphql_sync, load_schema_from_path, make_executable_schema, \
    snake_case_fallback_resolvers
"""NOTE:
GraphQL Playground constant (PLAYGROUND_HTML) was removed in Ariadne >=0.19.
We embed a minimal GraphiQL interface instead for interactive querying.
"""
from flask import request, jsonify
from api.operations import object_types
from config import cfg
from utils.cron import start_scheduler
import schedules
from api.medias.routes import *
from api.translations.routes import *
from api.blueprints import media, translations
import redis
import time


# Connect to Redis (optional)
redis_client = None
if cfg.get('redis', {}).get('active', False):
    try:
        redis_client = redis.Redis(host=cfg['redis']['host'], port=cfg['redis']['port'], db=0)
    except Exception as e:
        logger.error(f"Error connecting to Redis: {e}")

# Function to acquire a lock
def acquire_lock(lock_name, expire_time=60):
    if redis_client is None:
        return True  # No Redis: allow scheduler to start freely
    try:
        lock_acquired = redis_client.set(lock_name, 'LOCK', ex=expire_time, nx=True)
    except Exception as e:
        logger.error(f"Error acquiring lock for scheduler: {e}")
        lock_acquired = False
    return lock_acquired

# Function to release a lock
def release_lock(lock_name):
    if redis_client is not None:
        redis_client.delete(lock_name)

# Add a sleep period before starting the scheduler
if (cfg['cron']['active']) and acquire_lock('scheduler_lock'):
    try:
        # Set an environment variable to indicate this process as the scheduler worker
        os.environ['IS_SCHEDULER_WORKER'] = 'true'

        # Sleep only when using Redis to ensure only one worker starts the scheduler
        if redis_client is not None:
            time.sleep(5)

        start_scheduler()
    finally:
        release_lock('scheduler_lock')
else:
    logger.setup('cron disabled or already started by another worker')
type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(
    type_defs, object_types,  snake_case_fallback_resolvers
)

# Minimal GraphiQL HTML (served on GET /graphql). Uses CDN assets.
GRAPHIQL_HTML = """<!DOCTYPE html>
<html>
    <head>
        <meta charset=\"utf-8\" />
        <title>GraphiQL</title>
        <link rel=\"stylesheet\" href=\"https://unpkg.com/graphiql/graphiql.min.css\" />
        <style>body { margin:0; height:100vh; }</style>
    </head>
    <body>
        <div id=\"graphiql\" style=\"height:100vh;\"></div>
        <script src=\"https://unpkg.com/react/umd/react.production.min.js\"></script>
        <script src=\"https://unpkg.com/react-dom/umd/react-dom.production.min.js\"></script>
        <script src=\"https://unpkg.com/graphiql/graphiql.min.js\"></script>
        <script>
            const fetcher = params => fetch('/graphql', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params),
                    credentials: 'same-origin'
                }).then(r => r.json());
            ReactDOM.render(
                React.createElement(GraphiQL, { fetcher }),
                document.getElementById('graphiql')
            );
        </script>
    </body>
</html>"""

@app.route("/graphql", methods=["GET"])
def graphql_graphiql():
    """Serve GraphiQL IDE for interactive GraphQL queries."""
    return GRAPHIQL_HTML, 200

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
    response = jsonify(result)
    response.status_code = status_code
    # Add Cache-Control header
    response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
    
    return response
    

app.register_blueprint(media)
app.register_blueprint(translations)

if __name__ == "__main__":
    log = logging.getLogger('werkzeug')
    log.disabled = True
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    logger.start(
        f"Server is running on http://{cfg['flask']['host']}:{cfg['flask']['port']}\n" \
    f"GraphiQL IDE available at http://{cfg['flask']['host']}:{cfg['flask']['port']}/graphql\n"
        )
    app.run(host=cfg['flask']['host'], port=cfg['flask']['port'], debug=False)