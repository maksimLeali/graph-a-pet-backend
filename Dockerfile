FROM python:3.8-slim-buster
COPY . /app/
WORKDIR /app
RUN pip install --upgrade pip setuptools
RUN pip install -r requirements.txt

COPY config.yml ./alembic/
COPY db_scheme.json ./alembic/
# We copy everything in thge sub dir app





