from pendulum import SECONDS_PER_MINUTE
from api import app
from utils.logger import logger
import os
import logging
from ariadne import graphql_sync, load_schema_from_path, make_executable_schema, \
    snake_case_fallback_resolvers
from ariadne.constants import PLAYGROUND_HTML
from flask import request, jsonify
from api.operations import object_types
from config import cfg
from utils.firebase.storage import upload_image
from utils.cron import start_scheduler
import schedules
from api.medias.routes import *
from api.translations.routes import *
from api.blueprints import media, translations
import redis
import time


# Connect to Redis
try : 

    redis_client = redis.Redis(host=cfg['redis']['host'], port=cfg['redis']['port'], db=0)
except Exception as e:
    logger.error(f"Error connecting to Redis: {e}")
    redis_client = None
    
# Function to acquire a lock
def acquire_lock(lock_name, expire_time=60):
    logger.error('Acquiring lock for scheduler')

    lock_acquired = redis_client.set(lock_name, 'LOCK', ex=expire_time, nx=True)
    
    logger.error('Acquiried lock for scheduler')
    
    return lock_acquired

# Function to release a lock
def release_lock(lock_name):
    redis_client.delete(lock_name)

# Add a sleep period before starting the scheduler
if (cfg['cron']['active']) and acquire_lock('scheduler_lock'):
    try:
        # Set an environment variable to indicate this process as the scheduler worker
        os.environ['IS_SCHEDULER_WORKER'] = 'true'
        
        # Add a sleep period to ensure only one worker starts the scheduler
        time.sleep(5)  # Adjust the sleep duration as needed
        
        start_scheduler()
    finally:
        release_lock('scheduler_lock')
else:
    logger.setup('cron disabled or already started by another worker')
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
        f"See playground on http://{cfg['flask']['host']}:{cfg['flask']['port']}/graphql\n"
        )
    app.run(host=cfg['flask']['host'], port=cfg['flask']['port'], debug=False)