#!/bin/sh
echo 'waiting'

while ! mysqladmin ping -h"database" --silent; do
  sleep 1
done

alembic upgrade head

# Start the backend...