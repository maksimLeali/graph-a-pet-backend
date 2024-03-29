FROM python:3.8-slim-buster
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY db_scheme.json ./alembic/

ENV GUNICORN_CMD_ARGS="--workers 4 --bind 0.0.0.0:5000 --preload"
COPY . /app/
WORKDIR app/

CMD ["gunicorn", "app:app"]


