#!/bin/sh
echo 'waiting'

while ! mysqladmin ping -h"postgres" --silent; do
  sleep 1
done
cd alembic
alembic upgrade head
cd ..
# Start the backend...