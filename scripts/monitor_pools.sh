#!/bin/bash

while true; do
    echo "=== $(date) ==="
    echo "=== POOLS ==="
    PGPASSWORD=${POSTGRES_PASSWORD} psql -h pgbouncer -p 6432 -U ${POSTGRES_USER} -d pgbouncer -c "SHOW POOLS;"
    echo "=== CLIENTS ==="
    PGPASSWORD=${POSTGRES_PASSWORD} psql -h pgbouncer -p 6432 -U ${POSTGRES_USER} -d pgbouncer -c "SHOW CLIENTS;"
    echo "=== SERVERS ==="
    PGPASSWORD=${POSTGRES_PASSWORD} psql -h pgbouncer -p 6432 -U ${POSTGRES_USER} -d pgbouncer -c "SHOW SERVERS;"
    echo "=== STATS ==="
    PGPASSWORD=${POSTGRES_PASSWORD} psql -h pgbouncer -p 6432 -U ${POSTGRES_USER} -d pgbouncer -c "SHOW STATS;"
    echo "==================="
    sleep 5
done 