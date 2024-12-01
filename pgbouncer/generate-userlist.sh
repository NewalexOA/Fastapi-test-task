#!/bin/sh
# PostgreSQL MD5 hash is: md5 + md5(password + username)
echo "Environment variables:"
echo "POSTGRES_USER: ${POSTGRES_USER}"
echo "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}"

PGPASSWORD_HASH=$(echo -n "${POSTGRES_PASSWORD}${POSTGRES_USER}" | md5sum | cut -d' ' -f1)
echo "Generated hash: ${PGPASSWORD_HASH}"
echo "\"${POSTGRES_USER}\" \"md5${PGPASSWORD_HASH}\"" > /etc/pgbouncer/userlist.txt
echo "Generated userlist.txt:"
cat /etc/pgbouncer/userlist.txt 