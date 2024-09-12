# Run Alembic migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start the Gunicorn server
echo "Starting Gunicorn server..."
exec "$@"