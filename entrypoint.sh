#!/bin/bash

# Ждем доступности базы данных через pgbouncer
until PGPASSWORD=${POSTGRES_PASSWORD} psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - checking pgbouncer"

# Проверяем доступность pgbouncer
until PGPASSWORD=${POSTGRES_PASSWORD} psql -h pgbouncer -p 6432 -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c '\q'; do
  echo "PgBouncer is unavailable - sleeping"
  sleep 1
done

echo "PgBouncer is up - executing migrations"

# Запускаем миграции напрямую через PostgreSQL
cd /liquibase
liquibase \
  --changelog-file=changelog/changelog.xml \
  --url=jdbc:postgresql://db:5432/${POSTGRES_DB} \
  --username=${POSTGRES_USER} \
  --password=${POSTGRES_PASSWORD} \
  update

# Проверяем успешность миграций
until PGPASSWORD=${POSTGRES_PASSWORD} psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT count(*) FROM public.databasechangeloglock;" > /dev/null 2>&1; do
  echo "Waiting for migrations to complete..."
  sleep 2
done

# Проверяем доступность PgBouncer после миграций
until PGPASSWORD=${POSTGRES_PASSWORD} psql -h pgbouncer -p 6432 -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c '\q'; do
  echo "PgBouncer is not ready - waiting..."
  sleep 1
done

echo "Migrations completed - starting application"

cd /app
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 12 --loop uvloop --http httptools --backlog 2048 --limit-concurrency 400 