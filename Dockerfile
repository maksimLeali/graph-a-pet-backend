FROM python:3.8-slim-buster
COPY requirements.txt ./
RUN pip install -r requirements.txt

ENV GUNICORN_CMD_ARGS="--workers 4 --bind 0.0.0.0:5000"

COPY config.yml ./alembic/
COPY db_scheme.json ./alembic/
# We copy everything in thge sub dir app

CMD ["gunicorn", "app:app"]



