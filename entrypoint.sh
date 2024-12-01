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
  --url=jdbc:postgresql://db:5432/${POSTGRES_DB} \
  --username=${POSTGRES_USER} \
  --password=${POSTGRES_PASSWORD} \
  update

# Проверяем успешность миграций через запрос к БД
until PGPASSWORD=${POSTGRES_PASSWORD} psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT count(*) FROM public.databasechangeloglock;" > /dev/null 2>&1; do
  echo "Waiting for migrations to complete..."
  sleep 2
done

# Дополнительная проверка, что все миграции применены
PGPASSWORD=${POSTGRES_PASSWORD} psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT count(*) FROM public.databasechangelog;" > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Migration tables not found"
  exit 1
fi

echo "Migrations completed - starting application"

cd /app
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 12 --loop uvloop --http httptools --backlog 2048 --limit-concurrency 400 