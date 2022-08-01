FROM python:3.8-slim-buster

RUN pip install --upgrade pip setuptools
COPY config.yml ./alembic/
COPY db_scheme.json ./alembic/
# We copy everything in thge sub dir app
COPY . /app/

WORKDIR /app
RUN cd ./alembic
RUN alembic upgrade head
RUN cd ..


RUN pip install -r requirements.txt

