FROM python:3.8-slim-buster
COPY . /app/
RUN pip install --upgrade pip setuptools
RUN pip install -r requirements.txt

COPY ./app/config.yml ./app/alembic/
COPY ./app/db_scheme.json ./app/alembic/
# We copy everything in thge sub dir app

WORKDIR /app




