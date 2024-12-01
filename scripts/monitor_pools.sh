#!/bin/bash

while true; do
    echo "=== $(date) ==="
    
    PGPASSWORD=${POSTGRES_PASSWORD} psql -t -h pgbouncer -p 6432 -U wallet_user pgbouncer <<EOF
    \echo === POOLS ===
    SHOW POOLS;
    \echo === STATS ===
    SHOW STATS;
    \echo === LISTS ===
    SHOW LISTS;
    \echo === CLIENTS ===
    SHOW CLIENTS;
    \echo === SERVERS ===
    SHOW SERVERS;
    \echo === TRANSACTIONS ===
    SHOW TOTALS;
    \echo === AVERAGES ===
    SHOW STATS_AVERAGES;
    \echo === STATE ===
    SHOW STATE;
EOF
    
    echo "==================="
    sleep 5
done 