FROM python:3-alpine

RUN pip install --upgrade pip setuptools

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python3" ]

CMD [ "-m gunicorn --workers 4 --bind 0.0.0.0:5000 app:app" ]