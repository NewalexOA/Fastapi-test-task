#!/bin/sh
# PostgreSQL MD5 hash is: md5 + md5(password + username)

PGPASSWORD_HASH=$(echo -n "${POSTGRES_PASSWORD}${POSTGRES_USER}" | md5sum | cut -d' ' -f1)
echo "\"${POSTGRES_USER}\" \"md5${PGPASSWORD_HASH}\"" > /etc/pgbouncer/userlist.txt

# Generate pgbouncer.ini from template
cp /etc/pgbouncer/pgbouncer.ini /etc/pgbouncer/pgbouncer.ini.tmp
sed "s/\${POSTGRES_USER}/${POSTGRES_USER}/g" /etc/pgbouncer/pgbouncer.ini.tmp > /etc/pgbouncer/pgbouncer.ini
rm /etc/pgbouncer/pgbouncer.ini.tmp
