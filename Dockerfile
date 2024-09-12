# Use the base Python image
FROM python:3.8-slim-buster

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app will run on
EXPOSE 5000

# Set environment variables for Gunicorn
ENV GUNICORN_CMD_ARGS="--workers 10 --bind 0.0.0.0:5000"

# Run Alembic migrations before starting the app
CMD alembic upgrade head && gunicorn app:app
