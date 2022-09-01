FROM python:3.8-slim-buster

RUN pip install --upgrade pip setuptools
COPY config.yml ./alembic/
COPY db_scheme.json ./alembic/
RUN cd alembic && alembic upgrade head && cd ..
# We copy everything in thge sub dir app
COPY . /app/

WORKDIR /app
RUN pip install -r requirements.txt




