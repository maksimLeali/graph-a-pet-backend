FROM python:3.8-slim-buster

RUN pip install --upgrade pip setuptools

# We copy everything in thge sub dir app
COPY . /app/

WORKDIR /app

RUN pip install -r requirements.txt

<<<<<<< HEAD
COPY . /app

ENTRYPOINT [ "python3" ]

CMD [ "-m gunicorn --workers 4 --bind 0.0.0.0:5000 app:app" ]
=======
CMD [ "-m gunicorn --workers 4 --bind 0.0.0.0:5000 app:app" ]
>>>>>>> bc7104a4c3ed5381e0e7b17e6632e479a4e1aff4
