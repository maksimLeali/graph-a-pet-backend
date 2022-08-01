FROM python:3.8-slim-buster

RUN pip install --upgrade pip setuptools
COPY config.yml ./alembic/
COPY db_scheme.jso ./alembic/
# We copy everything in thge sub dir app
COPY . /app/

WORKDIR /app

RUN pip install -r requirements.txt

