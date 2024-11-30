#!/bin/bash

# Ждем доступности базы данных
until PGPASSWORD=${POSTGRES_PASSWORD} psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c '\q'; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Postgres is up - executing migrations"

# Запускаем миграции
cd /liquibase
liquibase \
  --changelog-file=changelog/changelog.xml \
  update

# Запускаем приложение
cd /app
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 