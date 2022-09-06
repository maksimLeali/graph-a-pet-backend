FROM python:3.8-slim-buster
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY config.yml ./alembic/
COPY db_scheme.json ./alembic/

COPY . /app/

WORKDIR app/


