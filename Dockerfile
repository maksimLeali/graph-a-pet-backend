FROM python:3.8-slim-buster

RUN pip install --upgrade pip setuptools

# We copy everything in thge sub dir app
COPY . /app/

WORKDIR /app

RUN pip install -r requirements.txt


RUN "python3 -m gunicorn --workers 4 --bind 0.0.0.0:5000 app:app"
