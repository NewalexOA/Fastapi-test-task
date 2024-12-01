#!/bin/bash

# Waiting for the database to be available through pgbouncer
until PGPASSWORD=${POSTGRES_PASSWORD} psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - checking pgbouncer"

# Checking the availability of pgbouncer
until PGPASSWORD=${POSTGRES_PASSWORD} psql -h pgbouncer -p 6432 -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c '\q'; do
  echo "PgBouncer is unavailable - sleeping"
  sleep 1
done

echo "PgBouncer is up - executing migrations"

# Running migrations directly through PostgreSQL
cd /liquibase
liquibase \
  --changelog-file=changelog/changelog.xml \
  --url=jdbc:postgresql://db:5432/${POSTGRES_DB} \
  --username=${POSTGRES_USER} \
  --password=${POSTGRES_PASSWORD} \
  update

# Checking the success of migrations
until PGPASSWORD=${POSTGRES_PASSWORD} psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT count(*) FROM public.databasechangeloglock;" > /dev/null 2>&1; do
  echo "Waiting for migrations to complete..."
  sleep 2
done

# Checking the availability of PgBouncer after migrations
until PGPASSWORD=${POSTGRES_PASSWORD} psql -h pgbouncer -p 6432 -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c '\q'; do
  echo "PgBouncer is not ready - waiting..."
  sleep 1
done

echo "Migrations completed - starting application"

cd /app
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 12 --loop uvloop --http httptools --backlog 2048 --limit-concurrency 400 