#!/bin/bash
PGPASSWORD_HASH=$(echo -n "${POSTGRES_PASSWORD}${POSTGRES_USER}" | md5sum | cut -d' ' -f1)
echo "\"${POSTGRES_USER}\" \"md5${PGPASSWORD_HASH}\"" > /etc/pgbouncer/userlist.txt 