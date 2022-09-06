FROM python:3.8-slim-buster
COPY requirements.txt ./
RUN pip install -r .requirements.txt
COPY . ./app
WORKDIR /app

COPY config.yml ./alembic/
COPY db_scheme.json ./alembic/
# We copy everything in thge sub dir app





